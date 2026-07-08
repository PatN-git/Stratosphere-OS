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

def block_hash(text, block_id):
    """Computes the SHA-256 hash of the inter-marker content for block_id in text.
    
    Worked example:
    If text contains:
    <!-- SOS:BLOCK id=test v=1.0.0 -->
    Hello World
    <!-- SOS:/BLOCK id=test -->
    The inter-marker content is normalized to "Hello World".
    SHA-256 hash: a830d7ecc05822b720977c4db35925f300c01fa4454c54d15ab9479346b7c1a0
    """
    normalized_text = normalize(text)
    lines = normalized_text.split("\n")
    start_line_idx = -1
    end_line_idx = -1
    start_re = re.compile(r'<!--\s*SOS:BLOCK\s+id=' + re.escape(block_id) + r'(?:\s+v=[^\s>]+)?\s*-->')
    end_re = re.compile(r'<!--\s*SOS:/BLOCK\s+id=' + re.escape(block_id) + r'\s*-->')
    
    for i, line in enumerate(lines):
        if start_re.search(line):
            start_line_idx = i
            break
            
    for i, line in enumerate(lines):
        if end_re.search(line):
            end_line_idx = i
            break
            
    if start_line_idx == -1 or end_line_idx == -1 or start_line_idx >= end_line_idx:
        raise ValueError(f"Block '{block_id}' markers not found or malformed")
        
    inter_lines = lines[start_line_idx + 1:end_line_idx]
    content = "\n".join(inter_lines)
    content = content.strip("\n")
    return hashlib.sha256(content.encode("utf-8")).hexdigest()

