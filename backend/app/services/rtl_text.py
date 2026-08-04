"""
RTL text preparation.

ReportLab (and PDF rendering generally) doesn't understand Arabic-script
text out of the box in two separate ways:
1. Glyph shaping — Persian/Arabic letters change shape depending on their
   position in a word (isolated/initial/medial/final form). Text needs to
   be "reshaped" into the correct connected glyph forms before rendering.
2. Bidi reordering — Arabic-script text flows right-to-left, but Unicode
   strings are stored in logical (reading) order, not visual order. The
   text needs to be reordered for correct visual display.

arabic_reshaper handles (1), python-bidi handles (2). Both are needed;
either alone produces incorrect output.
"""

import re

import arabic_reshaper
from bidi.algorithm import get_display

# Unicode ranges covering Persian/Arabic script. Used to detect whether a
# string needs RTL processing at all — running English text through the
# reshaper/bidi pipeline is unnecessary and could alter its formatting.
_RTL_PATTERN = re.compile(r"[\u0600-\u06FF\u0750-\u077F\uFB50-\uFDFF\uFE70-\uFEFF]")


def contains_rtl(text: str) -> bool:
    return bool(_RTL_PATTERN.search(text))


def prepare_rtl_text(text: str) -> str:
    """
    Reshapes and reorders text for correct PDF rendering if it contains
    Persian/Arabic characters. Text without any RTL characters is
    returned unchanged.

    Note: this applies reshaping/reordering to the whole string when ANY
    RTL character is present. For strings that mix long runs of Latin
    and Arabic-script text in complex ways, this is a reasonable
    approximation rather than a fully general bidi implementation — it
    correctly handles the common cases (a mostly-Persian line, a
    mostly-English line, or Persian text with embedded numbers/short
    English terms), which covers real-world dataset content well.
    """
    if not contains_rtl(text):
        return text

    reshaped = arabic_reshaper.reshape(text)
    result = get_display(reshaped)

    if isinstance(result, bytes):
        result = result.decode("utf-8")

    return result
