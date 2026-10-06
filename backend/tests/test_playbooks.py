import pytest

from app.rules.engine import analyze
from app.rules.playbooks import PLAYBOOK_MIN_MATCHES, PLAYBOOKS

CASES = {
    "fake_internship": "Congratulations! You are selected for internship at XYZ Pvt Ltd. No interview needed. Pay Rs 999 registration fee to confirm. Contact hr.xyz@gmail.com on WhatsApp",
    "fake_scholarship": "NSP scholarship approved. You have been selected. Pay Rs 500 processing fee to unlock and claim your scholarship amount at http://nsp-scholarship.xyz",
    "kyc_block": "Dear customer your account will be blocked today. Update KYC now at http://sbi-kyc-update.xyz",
    "upi_collect": "To receive Rs 5000 refund scan this QR and enter your UPI PIN",
    "fake_job_task": "Part time job! Complete simple tasks like rate hotels on Google Maps and earn Rs 3000 per day. Join telegram group",
    "parcel": "Your parcel is held at customs. Pay redelivery fee at http://bit.ly/abc123 within 24 hours",
    "lottery_reward": "Congratulations you won the lucky draw prize of Rs 25 lakh. Claim your prize, pay Rs 2000 to release the amount",
    "investment_group": "Join our VIP stock trading group. Guaranteed returns, daily profit, sure shot tips on WhatsApp",
}


def test_threshold_is_two():
    assert PLAYBOOK_MIN_MATCHES == 2


def test_there_is_a_test_for_every_playbook():
    assert {p["id"] for p in PLAYBOOKS} == set(CASES)


@pytest.mark.parametrize("pid", sorted(CASES))
def test_right_playbook_is_chosen(pid):
    r = analyze(CASES[pid])
    assert r.playbook is not None, [f.id for f in r.findings]
    assert r.playbook.id == pid
    assert len(r.playbook.how_it_works) == 3
    assert 2 <= len(r.playbook.what_next) <= 3
    assert 1 <= len(r.playbook.real_looks_like) <= 2


def test_playbook_follows_message_language():
    assert "KYC" in analyze("Aapka account block ho jayega. Turant KYC update karo aur OTP batao").playbook.name
    hi = analyze("आपका खाता बंद हो जाएगा। केवाईसी तुरंत अपडेट करें। अपना ओटीपी बताओ।").playbook
    assert hi and "स्कैम" in hi.name


def test_safe_message_has_no_playbook():
    assert analyze("Hey, are we meeting at 5 for the project discussion?").playbook is None
    assert analyze("Your internal exam results are out. Check https://mycollege.ac.in/results").playbook is None


def test_vague_message_has_no_playbook():
    r = analyze("Please share your OTP")  # one finding only: scary, but not enough to name a scam type
    assert r.verdict == "high_risk" and r.playbook is None


def test_playbook_data_is_complete_and_names_no_real_company():
    banned = ["sbi", "hdfc", "icici", "paytm", "phonepe", "amazon", "flipkart", "tcs", "infosys", "wipro"]
    for p in PLAYBOOKS:
        assert len(p["finding_ids"]) >= 2
        for key in ("name", "how_it_works", "what_next", "real_looks_like"):
            for lang in ("en", "hi", "hinglish"):
                assert p[key][lang], (p["id"], key, lang)
        blob = " ".join(str(p[k]).lower() for k in ("name", "how_it_works", "what_next", "real_looks_like"))
        assert not [b for b in banned if b in blob], p["id"]
