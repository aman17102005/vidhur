"""Tiny language guesser: 'hi' (Devanagari), 'hinglish' (Hindi in Latin letters) or 'en'. No network, no models."""
import re

_DEVANAGARI = re.compile(r"[ऀ-ॿ]")
_HINGLISH_WORDS = set(
    """aap aapka aapki aapke aapko apna apni hai hain hoga hogi jayega jaayega karo karein kijiye kijiyega
    bhejo bhej batao bata btao turant jaldi abhi paise paisa rupaye nahi nahin mat warna dijiye dena khata
    wala wali tumhara tumhare kya kyun lekin aur""".split()
)
# Common English words that also appear in the set above; ignore them when counting.
_AMBIGUOUS = {"bata", "dena", "aur"}


def detect_language(text: str) -> str:
    letters = sum(c.isalpha() for c in text) or 1
    if len(_DEVANAGARI.findall(text)) / letters > 0.2:
        return "hi"
    words = set(re.findall(r"[a-z]+", text.lower())) - _AMBIGUOUS
    if len(words & _HINGLISH_WORDS) >= 2:
        return "hinglish"
    return "en"
