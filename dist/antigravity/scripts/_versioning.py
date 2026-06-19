import hashlib
import re

SEMVER = re.compile(r"^\d+\.\d+\.\d+$")

def normalize(text):
    if text.startswith("\ufeff"):            # strip UTF-8 BOM
        text = text[1:]
    return text.replace("\r\n", "\n").replace("\r", "\n")   # LF only

def split_frontmatter(text):
    m = re.match(r"^---\n(.*?)\n---\n?(.*)$", text, re.S)
    if m:
        return m.group(1), m.group(2)
    return None, text

def read_version(text, path):
    """Extracts (version, timestamp) from YAML frontmatter."""
    text = normalize(text)
    
    fm, _ = split_frontmatter(text)
    if fm is not None:
        v_match = re.search(r'^version:\s*"?([^"\n\s]+)"?', fm, re.M)
        ts_match = re.search(r'^timestamp:\s*"?([^"\n\s]+)"?', fm, re.M)
        if v_match:
            return v_match.group(1), (ts_match.group(1) if ts_match else "")
            
    return None, None

def body_hash(text):
    # remove ONLY this file's plugin-version metadata so a version bump alone never changes the hash.
    text = normalize(text)
    fm, body = split_frontmatter(text)
    if fm is not None:
        # Strip version and timestamp
        fm = "\n".join(l for l in fm.split("\n")
                       if l.split(":", 1)[0].strip() not in ("version", "timestamp"))
        text = f"---\n{fm}\n---\n{body}" if fm.strip() else f"---\n---\n{body}"
    return hashlib.sha256(text.encode("utf-8")).hexdigest()
