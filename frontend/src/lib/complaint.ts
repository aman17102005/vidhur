// Builds the complaint draft text. Pure function: no network, no storage, no logging.
// Everything the user types stays in this browser tab's memory.

export interface ComplaintInput {
  date: string; // yyyy-mm-dd from <input type="date">, or ""
  caseSummary: string; // plain-English description of what happened
  amount: string; // digits the user typed, or ""
  message: string; // pasted scam message, or ""
}

function formatDate(iso: string): string {
  const m = /^(\d{4})-(\d{2})-(\d{2})$/.exec(iso);
  return m ? `${m[3]}/${m[2]}/${m[1]}` : "[date]";
}

export function buildComplaint(i: ComplaintInput): string {
  const amount = i.amount.replace(/[^\d.]/g, "");
  const lines = [
    "To,",
    "The Cyber Crime Cell / National Cyber Crime Reporting Portal",
    "",
    "Subject: Complaint about an online fraud",
    "",
    "I am reporting an online fraud that happened to me.",
    "",
    `Date of incident: ${formatDate(i.date)}`,
    `What happened: ${i.caseSummary}`,
    `Amount lost: ${amount ? "Rs " + amount : "[amount, or none]"}`,
    "Transaction ID / UPI reference: [fill in]",
    "Phone number / UPI ID / website of the other party: [fill in]",
  ];
  const msg = i.message.trim();
  if (msg) {
    lines.push("", "Message I received:", '"""', msg, '"""');
  }
  lines.push(
    "",
    "I have kept screenshots and the chat as evidence. I request you to please take action and help me stop or recover the payment.",
    "",
    "Name: [your name]",
    "Phone: [your phone number]",
  );
  return lines.join("\n");
}
