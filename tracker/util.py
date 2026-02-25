from __future__ import annotations

import re


def normalize_name(name: str) -> str:
    return re.sub(r"\s+", " ", name.strip()).casefold()


def parse_swim_time_to_centiseconds(raw: str) -> int | None:
    value = raw.strip()
    if not value:
        return None

    m = re.match(r"^(?:(\d+):)?(\d{1,2})\.(\d{2})$", value)
    if not m:
        return None
    minutes = int(m.group(1) or 0)
    seconds = int(m.group(2))
    centiseconds = int(m.group(3))
    return ((minutes * 60) + seconds) * 100 + centiseconds
