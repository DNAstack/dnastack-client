from typing import List


def get_visual_length(s: str) -> int:
    """Get the visual length of a string, ignoring ANSI escape codes."""
    # Remove ANSI escape sequences using regex
    import re

    ansi_escape = re.compile(r"\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])")
    return len(ansi_escape.sub("", s))


def wrap_text(text: str, width: int) -> List[str]:
    """Wrap text to specified width."""
    words = text.split()
    parts = []
    current_line = []
    current_length = 0

    for word in words:
        if current_length + len(word) + 1 <= width:
            current_line.append(word)
            current_length += len(word) + 1
        else:
            if current_line:
                parts.append(" ".join(current_line))
            current_line = [word]
            current_length = len(word)

    if current_line:
        parts.append(" ".join(current_line))

    return parts
