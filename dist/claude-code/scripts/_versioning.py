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
    """Extracts (version, updated) and determines form ('A', 'B', or None)."""
    text = normalize(text)
    # Check Form B first
    m = re.match(r'\A<!-- stratosphere: version=([^\s]+) updated=([^\s]+) -->\n', text)
    if m:
        return m.group(1), m.group(2), "B"
    
    # Check Form A
    fm, _ = split_frontmatter(text)
    if fm is not None:
        v_match = re.search(r'^version:\s*"?([^"\n\s]+)"?', fm, re.M)
        u_match = re.search(r'^updated:\s*"?([^"\n\s]+)"?', fm, re.M)
        if v_match:
            return v_match.group(1), (u_match.group(1) if u_match else ""), "A"
            
    return None, None, None

def body_hash(text, form):
    # remove ONLY this file's plugin-version metadata so a version bump alone never changes the hash.
    text = normalize(text)
    if form == "A":                          # plugin metadata is in frontmatter — strip WITHIN that block only
        fm, body = split_frontmatter(text)
        if fm is not None:
            # Strip version and updated
            fm = "\n".join(l for l in fm.split("\n")
                           if l.split(":", 1)[0].strip() not in ("version", "updated"))
            text = f"---\n{fm}\n---\n{body}" if fm.strip() else f"---\n---\n{body}"
    elif form == "B":                        # strip a stratosphere comment ONLY if it is the first line
        text = re.sub(r'\A<!-- stratosphere:[^\n]*-->\n', '', text)
    return hashlib.sha256(text.encode("utf-8")).hexdigest()
