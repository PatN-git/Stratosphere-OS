"""Append a probe to the rendered board: dispatch keydown events and report selection/move state. No change to the page's own code."""
from pathlib import Path

src = Path(r"C:\t\v5board\repo\.tmp\render\board.html")
dst = Path(r"C:\t\v5board\repo\.tmp\render\keyprobe.html")
probe = """
<script>
window.addEventListener('load', function () {
  setTimeout(function () {
    var r = {};
    function key(k, mods) {
      var o = {key: k, bubbles: true, cancelable: true};
      for (var m in (mods || {})) o[m] = mods[m];
      var ev = new KeyboardEvent('keydown', o);
      document.dispatchEvent(ev);
      return ev.defaultPrevented;
    }
    r.sel0 = selectedCardId || null;
    r.ctrlJ_prevented = key('j', {ctrlKey: true});
    r.sel_after_ctrlJ = selectedCardId || null;
    r.ctrlL_prevented = key('l', {ctrlKey: true});
    r.altLeft_prevented = key('ArrowLeft', {altKey: true});
    r.sel_after_ctrlL_altLeft = selectedCardId || null;
    r.plainJ_prevented = key('j');
    r.sel_after_plainJ = selectedCardId || null;
    var before = document.getElementById('change-payload').value;
    r.ctrl1_prevented = key('1', {ctrlKey: true});
    r.payload_after_ctrl1 = document.getElementById('change-payload').value === before;
    r.meta2_prevented = key('2', {metaKey: true});
    r.payload_after_meta2 = document.getElementById('change-payload').value === before;
    r.plain2_prevented = key('2');
    r.payload_after_plain2 = document.getElementById('change-payload').value !== before;
    r.slash_prevented = key('/');
    r.ctrlK_prevented = key('k', {ctrlKey: true});
    var pre = document.createElement('pre');
    pre.id = 'probe-report';
    pre.textContent = JSON.stringify(r);
    document.body.appendChild(pre);
  }, 400);
});
</script>
"""
text = src.read_text(encoding="utf-8")
dst.write_text(text + probe, encoding="utf-8")
print("wrote", dst)
