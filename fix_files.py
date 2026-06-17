import re
from pathlib import Path

root = Path("C:/Users/patri/.gemini/antigravity/worktrees/Stratosphere-OS/review-versioning-system-plan")

def process_file(p: Path):
    if not p.name.endswith(".md"): return
    text = p.read_text(encoding="utf-8")
    
    # Check for HTML version comment and extract
    html_match = re.search(r'<!--\s*stratosphere:\s*version=([\d\.]+)\s*updated=([0-9\-]+)\s*-->\r?\n', text)
    if html_match:
        old_v = html_match.group(1)
        old_u = html_match.group(2)
        # Remove the HTML comment completely
        text = text[:html_match.start()] + text[html_match.end():]
        
        # Inject into YAML frontmatter if it exists
        if text.startswith("---"):
            # Check if version already exists
            if "version:" not in text.split("---")[1]:
                # Inject just before the second ---
                parts = text.split("---", 2)
                frontmatter = parts[1].rstrip()
                frontmatter += f'\nversion: "{old_v}"\nupdated: {old_u}\n'
                text = f"---{frontmatter}---{parts[2]}"
    
    # Now, bump the version!
    # If the file has a version: "x.y.z" tag, bump the patch version.
    def bump(match):
        v = match.group(1)
        parts = v.split(".")
        parts[-1] = str(int(parts[-1]) + 1)
        return f'version: "{".".join(parts)}"'
        
    text = re.sub(r'version:\s*"([\d\.]+)"', bump, text)
    
    p.write_text(text, encoding="utf-8")

# Process all files in src/
for md in (root / "src").rglob("*.md"):
    process_file(md)

print("Versions bumped and HTML comments stripped.")
