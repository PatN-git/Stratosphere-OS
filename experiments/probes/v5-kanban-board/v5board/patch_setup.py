from pathlib import Path

p = Path(__file__).resolve().parent / "setup_board.py"
lines = p.read_text(encoding="utf-8").split(chr(10))
i = next(n for n, l in enumerate(lines) if l.startswith("BODY = Path("))
lines[i:i + 3] = ['BODY = ROOT.parent / "body.md"', 'BODY.write_text("body" + chr(10), encoding="utf-8")']
p.write_text(chr(10).join(lines), encoding="utf-8")
print(lines[i - 1:i + 3])
