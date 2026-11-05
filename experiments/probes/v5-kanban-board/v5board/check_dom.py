"""Parse the headless-browser DOM dump of the board and report injection/escaping facts."""
import json
import sys
from html.parser import HTMLParser

path = sys.argv[1]
html = open(path, encoding="utf-8").read()


class P(HTMLParser):
    def __init__(self):
        super().__init__()
        self.imgs = []
        self.on_attrs = []
        self.scripts = []
        self.in_script = None
        self.texts = []
        self.stack = []

    def handle_starttag(self, tag, attrs):
        self.stack.append(tag)
        for k, v in attrs:
            if k.lower().startswith("on"):
                self.on_attrs.append((tag, k, (v or "")[:60]))
        if tag == "img":
            self.imgs.append(attrs)
        if tag == "script":
            self.in_script = {"attrs": dict(attrs), "text": ""}

    def handle_endtag(self, tag):
        if tag == "script" and self.in_script is not None:
            self.scripts.append(self.in_script)
            self.in_script = None
        if self.stack:
            self.stack.pop()

    def handle_data(self, data):
        if self.in_script is not None:
            self.in_script["text"] += data
        else:
            self.texts.append(data)


p = P()
p.feed(html)
print("img elements:", len(p.imgs))
print("elements with on* attributes:", p.on_attrs)
print("script blocks:", [(s["attrs"].get("type"), len(s["text"])) for s in p.scripts])
for s in p.scripts:
    if s["attrs"].get("type") == "application/json":
        raw = s["text"]
        print("data block raw has '</script' :", "</script" in raw.lower())
        data = json.loads(raw)
        cards = data.get("cards") or data.get("items") or data
        labels = [c.get("label") for c in cards] if isinstance(cards, list) else None
        print("json cards:", len(labels) if labels else type(cards))
        for l in labels or []:
            print("  ", repr(l))
text = " ".join(t.strip() for t in p.texts if t.strip())
for needle in ["Plain card", "C:\\new\\table", "PWNED", "Fish & chips", "Pre-fetch -> cache -> serve", "Line", "apostrophe"]:
    print(f"visible text has {needle!r}:", needle in text)
