import re,sys
sys.path.insert(0,'.tmp/bt189')
import importlib.util
src=open('.tmp/bt189/s2_count.py',encoding='utf-8').read().split("rows = []")[0]
exec(src)
for f in sys.argv[1:]:
    p=ROOT/f
    for i,line in enumerate(p.read_text(encoding='utf-8').splitlines(),1):
        if CORE.search(line):
            ss=[s for s in sentences(line) if CORE.search(s)]
            print(f"{f}:{i} line={len(line)} sent={sum(len(s)+1 for s in ss)} | "+" || ".join(s[:70] for s in ss))
