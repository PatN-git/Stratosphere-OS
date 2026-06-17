import sys
import json
import re
from pathlib import Path

def map_bundled_to_project(rel_path: str):
    parts = rel_path.split("/")
    if parts[0] == "assets" and parts[1] == "templates":
        sub = parts[2]
        name = parts[3]
        if sub == "constitution": return name
        elif sub == "memory": return f".memory/{name}"
        elif sub == "rules": return f".agents/rules/{name}"
        elif sub == "references": return f".agents/workflows/.reference/{name}"
    elif parts[0] in ("workflows", "commands", "skills"):
        if parts[0] in ("workflows", "commands"):
            # skip instantiate / sync-skills if they are mapped weirdly, but sync-skills goes to .agents/workflows/
            if name_is_lifecycle(parts[-1]):
                return f".agents/workflows/{parts[-1]}"
    return None

def name_is_lifecycle(name):
    return re.match(r"^[0-4].*\.md$", name) or name == "sync-skills.md"
