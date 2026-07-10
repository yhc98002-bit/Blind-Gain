from __future__ import annotations

import re
import unicodedata
from typing import Any


def normalize_ocr_text(value: Any) -> str:
    text = unicodedata.normalize("NFKC", str(value)).casefold().replace("<image>", " ")
    text = re.sub(r"[^\w]+", " ", text, flags=re.UNICODE)
    return " ".join(text.split())
