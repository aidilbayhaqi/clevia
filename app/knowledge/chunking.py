import re

def normalize_text(text: str) -> str:
    lines = [
        line.rstrip()
        for line in text.replace("\r\n", "\n").replace("\r", "\n").split("\n")
    ]
    output: list[str] = []
    blank = False
    for line in lines:
        cleaned = line.strip()
        if not cleaned:
            if output and not blank:
                output.append("")
            blank = True
            continue
        blank = False
        output.append(cleaned)
    return "\n".join(output).strip()


def semantic_chunks(text: str, max_chars: int | None = None) -> list[str]:
    max_chars = max_chars or 1200
    normalized = normalize_text(text)
    if not normalized:
        return []

    blocks = [block.strip() for block in re.split(r"\n\s*\n", normalized) if block.strip()]
    chunks: list[str] = []
    current = ""

    for block in blocks:
        if len(block) > max_chars:
            units = re.split(r"(?<=[.!?])\s+", block)
        else:
            units = [block]

        for unit in units:
            candidate = f"{current}\n\n{unit}".strip() if current else unit.strip()
            if current and len(candidate) > max_chars:
                chunks.append(current.strip())
                current = unit.strip()
            else:
                current = candidate

    if current:
        chunks.append(current.strip())
    return chunks
