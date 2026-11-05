"""Copy board.html and append a probe that reports live-DOM facts and drives moveCard(); no change to the page's own code."""
from pathlib import Path

src = Path(r"C:\t\v5board\repo\.tmp\render\board.html")
dst = Path(r"C:\t\v5board\repo\.tmp\render\probe.html")
IDS = {
    "plain": "BT-LOCAL-plain-card",
    "hyphen": "BT-LOCAL-pre-fetch-cache-serve",
    "script": "BT-LOCAL-script-img-src-x-onerror-document-title",
    "quotes": "BT-LOCAL-quote-and-and-tick",
}
probe = """
<script>
window.addEventListener('load', function () {
  setTimeout(function () {
    var r = {};
    r.title = document.title;
    r.imgs = document.querySelectorAll('img').length;
    r.onAttrs = Array.prototype.filter.call(document.querySelectorAll('*'), function (e) {
      return Array.prototype.some.call(e.attributes, function (a) { return a.name.indexOf('on') === 0; });
    }).length;
    r.labels = Array.prototype.map.call(document.querySelectorAll('.card-label'), function (e) { return e.textContent; });
    r.errors = window.__errs || [];
    try {
      moveCard('%(plain)s', 'in progress');
      moveCard('%(hyphen)s', 'needs_spec');
      moveCard('%(script)s', 'done');
      moveCard('%(quotes)s', 'blocked');
    } catch (e) { r.moveError = String(e); }
    setTimeout(function () {
      r.payload = document.getElementById('change-payload').value;
      r.imgsAfter = document.querySelectorAll('img').length;
      r.titleAfter = document.title;
      var pre = document.createElement('pre');
      pre.id = 'probe-report';
      pre.textContent = JSON.stringify(r);
      document.body.appendChild(pre);
    }, 400);
  }, 400);
});
window.__errs = [];
window.addEventListener('error', function (e) { window.__errs.push(String(e.message)); });
</script>
""" % IDS
text = src.read_text(encoding="utf-8")
dst.write_text(text + probe, encoding="utf-8")
print("wrote", dst)
