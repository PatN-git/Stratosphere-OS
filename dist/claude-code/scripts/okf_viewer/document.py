from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any

REQUIRED_FRONTMATTER_KEYS = ("type", "title", "description", "timestamp")

_FRONTMATTER_DELIM = "---"


class OKFDocumentError(ValueError):
    pass


def _parse_yaml(fm_text: str) -> dict[str, Any]:
    # Parse YAML frontmatter using standard library only
    result = {}
    lines = fm_text.splitlines()
    current_key = None
    list_items = []
    
    i = 0
    while i < len(lines):
        line = lines[i]
        # Ignore comments and empty lines
        if not line.strip() or line.strip().startswith('#'):
            i += 1
            continue
            
        # Check if line is a block list item under current_key (e.g. "  - item" or "- item")
        list_match = re.match(r'^(\s*)-\s+(.*)$', line)
        if list_match and current_key is not None:
            val = list_match.group(2).strip()
            if (val.startswith('"') and val.endswith('"')) or (val.startswith("'") and val.endswith("'")):
                val = val[1:-1]
            list_items.append(val)
            result[current_key] = list_items
            i += 1
            continue
            
        if ':' in line:
            # Transition to a new key, commit the previous list if we were in one
            current_key = None
            list_items = []
            
            k, v = line.split(':', 1)
            k = k.strip()
            v = v.strip()
            
            # Remove optional trailing comment if it's there
            if '#' in v:
                if not (v.startswith('"') or v.startswith("'")):
                    v = v.split('#', 1)[0].strip()
                    
            if v == '':
                current_key = k
                result[k] = None
            elif v.startswith('[') and v.endswith(']'):
                items_str = v[1:-1]
                items = []
                for item in items_str.split(','):
                    item = item.strip()
                    if (item.startswith('"') and item.endswith('"')) or (item.startswith("'") and item.endswith("'")):
                        item = item[1:-1]
                    if item:
                        items.append(item)
                result[k] = items
            else:
                if (v.startswith('"') and v.endswith('"')) or (v.startswith("'") and v.endswith("'")):
                    v = v[1:-1]
                if v.lower() == 'true':
                    result[k] = True
                elif v.lower() == 'false':
                    result[k] = False
                elif v.lower() == 'null' or v == '~':
                    result[k] = None
                else:
                    try:
                        if '.' in v:
                            result[k] = float(v)
                        else:
                            result[k] = int(v)
                    except ValueError:
                        result[k] = v
        i += 1
    return result


@dataclass
class OKFDocument:
    frontmatter: dict[str, Any] = field(default_factory=dict)
    body: str = ""

    @classmethod
    def parse(cls, text: str) -> "OKFDocument":
        lines = text.splitlines()
        if not lines or lines[0].strip() != _FRONTMATTER_DELIM:
            return cls(frontmatter={}, body=text)

        end_idx = None
        for i in range(1, len(lines)):
            if lines[i].strip() == _FRONTMATTER_DELIM:
                end_idx = i
                break
        if end_idx is None:
            raise OKFDocumentError("Unterminated YAML frontmatter block")

        fm_text = "\n".join(lines[1:end_idx])
        try:
            fm = _parse_yaml(fm_text)
        except Exception as e:
            raise OKFDocumentError(f"Invalid YAML in frontmatter: {e}") from e
        if not isinstance(fm, dict):
            raise OKFDocumentError("Frontmatter must be a YAML mapping")

        body = "\n".join(lines[end_idx + 1:])
        if body.startswith("\n"):
            body = body[1:]
        return cls(frontmatter=fm, body=body)

    def serialize(self) -> str:
        # A simple YAML dumper for frontmatter keys
        yaml_lines = []
        for k, v in self.frontmatter.items():
            if isinstance(v, list):
                yaml_lines.append(f"{k}:")
                for item in v:
                    yaml_lines.append(f"  - {item}")
            elif isinstance(v, bool):
                yaml_lines.append(f"{k}: {str(v).lower()}")
            elif v is None:
                yaml_lines.append(f"{k}: null")
            elif isinstance(v, (int, float)):
                yaml_lines.append(f"{k}: {v}")
            else:
                v_str = str(v)
                if any(char in v_str for char in [':', '{', '}', '[', ']', ',', '&', '*', '#', '?', '|', '-', '<', '>', '=', '!', '%', '@', '\\']) or v_str == "":
                    escaped = v_str.replace('"', '\\"')
                    yaml_lines.append(f"{k}: \"{escaped}\"")
                else:
                    yaml_lines.append(f"{k}: {v_str}")
        fm_text = "\n".join(yaml_lines)
        body = self.body if self.body.endswith("\n") else self.body + "\n"
        return f"{_FRONTMATTER_DELIM}\n{fm_text}\n{_FRONTMATTER_DELIM}\n\n{body}"

    def validate(self) -> None:
        missing = [k for k in REQUIRED_FRONTMATTER_KEYS if not self.frontmatter.get(k)]
        if missing:
            raise OKFDocumentError(
                f"Missing required frontmatter keys: {', '.join(missing)}"
            )
