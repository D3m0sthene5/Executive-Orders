"""Build the owner's worksheet: reference_entry.html (+ REFERENCE_SHEET.csv, AGREED.json).

Section 1: the owner passages (OWNER_SET.json): image crop, that crop's GPO text (read-only), a blank field.
Section 2: a spot-check of up to 10 passages on which GPO's layer and the reference engine agree exactly: image crop,
the agreed text pre-filled, 'correct as shown' / 'needs correction'.
Nothing is filled in for the owner. Images are referenced by their absolute path on this PC (file:// URLs), so open the
page from this PC. Progress is kept in the browser's localStorage while the page is open (best effort).
Run: C:/Users/danie/eo-venvs/enc/Scripts/python.exe -I make_reference_page.py [--ref-engine surya] [--spot 10]
"""
import argparse
import csv
import html
import json
import os
import random
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import score as S

CONVENTIONS = [
    "Type exactly what is printed, line by line, with the line breaks where the image breaks them.",
    "Fractions: type the single characters \u00bc \u00bd \u00be (buttons below the box). Keep \u00a7, degree \u00b0, minute \u2032 and second \u2033 marks.",
    "Keep printed spelling, punctuation, capitalization and end-of-line hyphens. Do not correct anything.",
    "A line cut off at the top or bottom edge of the crop: leave it out. A character you cannot read: write [illegible].",
    "Small capitals: type capital letters. A row of leader dashes, underscores or dots: type ... (three dots).",
    "Several columns: the left column first, then the next. A marginal note goes on its own line just before the "
    "main-text line it sits beside.",
]


def card(p, kind, text, n):
    img = "file:///" + p["crop_png_path"].replace("\\", "/")
    h = [f'<section class="card" id="c-{p["id"]}" data-id="{p["id"]}" data-kind="{kind}">']
    h.append(f'<h3>{n}. {p["id"]} <small>{html.escape(p["subtype"])} &middot; {html.escape(p["source_key"])} '
             f'p.{p["pdf_page"]}</small></h3>')
    h.append(f'<img src="{img}" alt="crop {p["id"]}" loading="lazy">')
    if kind == "owner":
        h.append('<details><summary>GPO text layer for this crop (for reference only; it contains errors)</summary>'
                 f'<pre>{html.escape(text)}</pre></details>')
        h.append('<textarea class="ref" rows="12" placeholder="Type the passage here" spellcheck="false"></textarea>')
    else:
        h.append('<p class="hint">Agreed text (GPO layer and the engine read it identically). Is it exactly what the image shows?</p>')
        h.append(f'<textarea class="ref" rows="12" spellcheck="false">{html.escape(text)}</textarea>')
        h.append('<label><input type="radio" name="ok-%s" value="yes"> correct as shown</label> '
                 '<label><input type="radio" name="ok-%s" value="no"> needs correction (edit the text above)</label>'
                 % (p["id"], p["id"]))
    h.append('<div class="keys">' + "".join(f'<button type="button" class="k" data-ch="{c}">{c}</button>'
                                           for c in "\u00bc\u00bd\u00be\u00a7\u00b0\u2032\u2033\u2013\u2014\u00b6") + "</div>")
    h.append("</section>")
    return "\n".join(h)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--ref-engine", default="surya")
    ap.add_argument("--spot", type=int, default=10)
    a = ap.parse_args()
    ps = S.load_passages(os.path.join(HERE, "PASSAGES.csv"))
    rd = S.load_readings(os.path.join(HERE, "READINGS.jsonl"))
    with open(os.path.join(HERE, "OWNER_SET.json"), encoding="utf-8") as fh:
        owner = json.load(fh)["ids"]
    agreed, dis = S.build_agreed(rd, ps, set(owner), a.ref_engine)
    rnd = random.Random(20261106)
    hard = sorted(i for i in agreed if ps[i]["category"] == "hard")
    clean = sorted(i for i in agreed if ps[i]["category"] == "clean")
    rnd.shuffle(hard)
    rnd.shuffle(clean)
    spot = []
    while len(spot) < min(a.spot, len(agreed)) and (hard or clean):
        for pool in (hard, clean):
            if pool and len(spot) < a.spot:
                spot.append(pool.pop())
    spot = sorted(spot)
    with open(os.path.join(HERE, "AGREED.json"), "w", encoding="utf-8", newline="\n") as fh:
        json.dump({"reference_engine": a.ref_engine, "rule": "GPO text layer and the engine's text identical after "
                   "whitespace folding (strict)", "n_agreed": len(agreed), "agreed_ids": sorted(agreed),
                   "n_disagreed_left_out": len(dis), "disagreed_ids": dis, "spot_check_ids": spot}, fh, indent=1)
    rows = []
    cards = []
    for n, pid in enumerate(owner, 1):
        p = ps[pid]
        cards.append(card(p, "owner", rd[pid]["gpo-layer"], n))
        rows.append({"section": "owner", "id": pid, "image_path": p["crop_png_path"], "proposed_text": "", "reference": ""})
    for n, pid in enumerate(spot, 1):
        p = ps[pid]
        cards.append(card(p, "spot", agreed[pid], n))
        rows.append({"section": "spot-check", "id": pid, "image_path": p["crop_png_path"], "proposed_text": agreed[pid],
                     "reference": ""})
    with open(os.path.join(HERE, "REFERENCE_SHEET.csv"), "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=["section", "id", "image_path", "proposed_text", "reference"])
        w.writeheader()
        w.writerows(rows)
    page = TEMPLATE.replace("%%CONV%%", "".join(f"<li>{html.escape(c)}</li>" for c in CONVENTIONS))
    page = page.replace("%%OWNER%%", "\n".join(cards[:len(owner)])).replace("%%SPOT%%", "\n".join(cards[len(owner):]))
    page = page.replace("%%NOWNER%%", str(len(owner))).replace("%%NSPOT%%", str(len(spot)))
    page = page.replace("%%ENGINE%%", html.escape(a.ref_engine))
    with open(os.path.join(HERE, "reference_entry.html"), "w", encoding="utf-8", newline="\n") as fh:
        fh.write(page)
    print("owner", len(owner), "spot", len(spot), "agreed", len(agreed), "left out", len(dis))


TEMPLATE = """<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>OCR reference worksheet</title>
<style>
:root{--bg:#fbfaf7;--fg:#1d1d1b;--mut:#6b6a63;--card:#fff;--line:#d9d6cc;--acc:#8a2b1c}
@media (prefers-color-scheme:dark){:root{--bg:#161614;--fg:#ece9e0;--mut:#a09d92;--card:#1f1f1c;--line:#3a3935;--acc:#e0866f}}
body{background:var(--bg);color:var(--fg);font:16px/1.45 Georgia,serif;margin:0 auto;max-width:980px;padding:16px}
h1{font-size:1.4rem;margin:.2em 0}h2{margin-top:1.6em;border-bottom:2px solid var(--acc);padding-bottom:.2em}
.card{background:var(--card);border:1px solid var(--line);border-radius:8px;padding:12px;margin:14px 0}
.card h3{margin:.1em 0 .5em;font-size:1.05rem}.card small{color:var(--mut);font-weight:normal}
img{max-width:100%;height:auto;border:1px solid var(--line);display:block;margin:6px 0}
textarea{width:100%;box-sizing:border-box;font:15px/1.4 Consolas,monospace;background:var(--bg);color:var(--fg);border:1px solid var(--line);border-radius:6px;padding:8px}
pre{white-space:pre-wrap;font:13px/1.35 Consolas,monospace;background:var(--bg);padding:8px;border-radius:6px;overflow:auto}
.keys button{font-size:1.1rem;margin:4px 4px 0 0;padding:2px 10px;cursor:pointer}
.bar{position:sticky;top:0;background:var(--bg);padding:8px 0;border-bottom:1px solid var(--line);z-index:5}
button.go{background:var(--acc);color:#fff;border:0;border-radius:6px;padding:8px 14px;margin-right:8px;cursor:pointer;font-size:1rem}
.hint{color:var(--mut);margin:.3em 0}ul{margin:.3em 0 .3em 1.2em}
.done{outline:2px solid #3b8a4d}
</style></head><body>
<h1>OCR reference worksheet</h1>
<p>Section 1 has <b>%%NOWNER%%</b> passages for you to type from the image. Section 2 has <b>%%NSPOT%%</b> quick checks of
text that GPO's layer and the %%ENGINE%% engine read identically. Plan: under an hour. Nothing here is pre-filled in
section 1. This page runs only on this PC (the images are local files).</p>
<details open><summary><b>How to type (same rules for every passage)</b></summary><ul>%%CONV%%</ul></details>
<div class="bar"><span id="prog">0 / 0 done</span> &nbsp;
<button class="go" id="exp1">Export section 1 (OWNER_REFERENCES.csv)</button>
<button class="go" id="exp2">Export section 2 (SPOTCHECK.csv)</button></div>
<h2>Section 1. Type these (%%NOWNER%%)</h2>
%%OWNER%%
<h2>Section 2. Spot-check (%%NSPOT%%)</h2>
%%SPOT%%
<script>
(function(){
var KEY="ventris-ocr-ref-v1", store={};
try{store=JSON.parse(localStorage.getItem(KEY)||"{}")}catch(e){store={}}
function save(){try{localStorage.setItem(KEY,JSON.stringify(store))}catch(e){}}
var cards=[].slice.call(document.querySelectorAll(".card"));
function rec(c){return store[c.dataset.id+"|"+c.dataset.kind]||(store[c.dataset.id+"|"+c.dataset.kind]={})}
function refresh(){
  var d=0;cards.forEach(function(c){var t=c.querySelector("textarea").value.trim();var r=c.querySelector("input[type=radio]:checked");
    var ok=c.dataset.kind==="owner"?t.length>0:!!r; c.classList.toggle("done",ok); if(ok)d++;});
  document.getElementById("prog").textContent=d+" / "+cards.length+" done";}
cards.forEach(function(c){
  var ta=c.querySelector("textarea"), r=rec(c);
  if(r.text!==undefined){ta.value=r.text}
  if(r.ok){var rb=c.querySelector("input[value="+r.ok+"]");if(rb)rb.checked=true}
  ta.addEventListener("input",function(){rec(c).text=ta.value;save();refresh()});
  [].forEach.call(c.querySelectorAll("input[type=radio]"),function(x){x.addEventListener("change",function(){rec(c).ok=x.value;save();refresh()})});
  [].forEach.call(c.querySelectorAll("button.k"),function(b){b.addEventListener("click",function(){
    var s=ta.selectionStart,e=ta.selectionEnd;ta.value=ta.value.slice(0,s)+b.dataset.ch+ta.value.slice(e);
    ta.selectionStart=ta.selectionEnd=s+b.dataset.ch.length;ta.focus();rec(c).text=ta.value;save();refresh()})});
});
function q(s){return '"'+String(s).replace(/"/g,'""')+'"'}
function dl(name,rows){var blob=new Blob(["\\ufeff"+rows.join("\\r\\n")+"\\r\\n"],{type:"text/csv;charset=utf-8"});
  var a=document.createElement("a");a.href=URL.createObjectURL(blob);a.download=name;document.body.appendChild(a);a.click();a.remove()}
document.getElementById("exp1").onclick=function(){var rows=["id,reference"];
  cards.filter(function(c){return c.dataset.kind==="owner"}).forEach(function(c){rows.push(q(c.dataset.id)+","+q(c.querySelector("textarea").value.replace(/\\r\\n/g,"\\n").trim()))});
  dl("OWNER_REFERENCES.csv",rows)};
document.getElementById("exp2").onclick=function(){var rows=["id,ok,corrected"];
  cards.filter(function(c){return c.dataset.kind==="spot"}).forEach(function(c){var r=c.querySelector("input[type=radio]:checked");
    var v=r?r.value:"";rows.push(q(c.dataset.id)+","+q(v)+","+q(v==="no"?c.querySelector("textarea").value.replace(/\\r\\n/g,"\\n").trim():""))});
  dl("SPOTCHECK.csv",rows)};
refresh();
})();
</script></body></html>
"""

if __name__ == "__main__":
    main()
