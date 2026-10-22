#!/usr/bin/env python3
"""tracker_switch.py — move a local-tracker project to GitHub (local -> GitHub only).

`write_tracker` records the backend as the `tracker:` frontmatter key of `.memory/ARCHITECTURE.md`.
"""
import re
from pathlib import Path


def write_tracker(path, value):
    """Set `tracker: <value>` in the frontmatter of `path`, keeping its line endings.
    True when the file changed. ValueError when the file has no frontmatter (nothing is written)."""
    text = Path(path).read_bytes().decode('utf-8-sig')
    eol = '\r\n' if '\r\n' in text else '\n'
    m = re.match(r'---\r?\n(.*?\r?\n)?---(?=\r?\n|$)', text, re.S)
    if not m:
        raise ValueError(f"{path} has no frontmatter to hold `tracker:`")
    head = m.group(1) or ''
    line = f"tracker: {value}"
    if re.search(r'^tracker:.*$', head, re.M):
        new_head = re.sub(r'^tracker:.*?(?=\r?$)', line, head, count=1, flags=re.M)
    else:
        new_head = head + line + eol
    if new_head == head:
        return False
    out = '---' + eol + new_head + text[m.end() - 3:]
    Path(path).write_bytes(out.encode('utf-8'))
    return True
