import ftfy
import re


def clean_text(text: str) -> str:
    if not text:
        return ""

    text = ftfy.fix_text(text)
    text = re.sub(r"\n{3,}", "\n\n", text).strip()
    return text
