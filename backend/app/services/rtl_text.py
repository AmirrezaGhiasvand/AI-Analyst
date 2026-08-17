"""
RTL text preparation.
"""

import re

import arabic_reshaper
from bidi.algorithm import get_display

_RTL_PATTERN = re.compile(r"[\u0600-\u06FF\u0750-\u077F\uFB50-\uFDFF\uFE70-\uFEFF]")


def contains_rtl(text: str) -> bool:
    return bool(_RTL_PATTERN.search(text))


def prepare_rtl_text(text: str) -> str:
    if not contains_rtl(text):
        return text
    reshaped = arabic_reshaper.reshape(text)
    return get_display(reshaped)