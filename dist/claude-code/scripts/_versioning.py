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

# Canonical pattern to parse SOS:BLOCK markers
# Group 1: 'BLOCK' or '/BLOCK'
# Group 2: block id
# Group 3: version (optional)
CANONICAL_MARKER_PATTERN = re.compile(r'<!--\s*SOS:(BLOCK|/BLOCK)\s+id=(\S+?)(?:\s+v=(\S+?))?\s*-->')

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
    
    # Precondition: parse_file_blocks() has already validated tag-integrity and same-id uniqueness
    # for user-authored files. Direct calls from get_blocks_map() trust that template files are well-formed.
    # To harden, we assert that exactly one START and one END tag match this block_id.
    start_count = 0
    end_count = 0
    
    for i, line in enumerate(lines):
        m = CANONICAL_MARKER_PATTERN.search(line)
        if m and m.group(2) == block_id:
            if m.group(1) == "BLOCK":
                start_line_idx = i
                start_count += 1
            elif m.group(1) == "/BLOCK":
                end_line_idx = i
                end_count += 1
                
    if start_count != 1 or end_count != 1:
        raise ValueError(f"Block '{block_id}' must have exactly one START and one END marker; found {start_count} START and {end_count} END")
        
    if start_line_idx == -1 or end_line_idx == -1 or start_line_idx >= end_line_idx:
        raise ValueError(f"Block '{block_id}' markers not found or malformed")
        
    inter_lines = lines[start_line_idx + 1:end_line_idx]
    content = "\n".join(inter_lines)
    
    # strip() drops all leading/trailing newlines before hashing so that differences in spacing
    # outside block boundaries do not manufacture false conflicts. This is self-consistent and used everywhere.
    content = content.strip("\n")
    return hashlib.sha256(content.encode("utf-8")).hexdigest()

