"""Offline tests for app_harvest parsing; no network."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import app_harvest as a

LISTING = """<div class="pager-last"></div><div class="view-content">
<div class="views-row views-row-1">
<div  about="/documents/executive-order-9066-authorizing-the-secretary-war-prescribe-military-areas" typeof="x" class="node">
<h4><span  property="dc:date" datatype="xsd:dateTime" content="1942-02-19T00:00:00+00:00">February 19, 1942</span></h4>
<div class="field-title">
<p><a href="/documents/executive-order-9066-authorizing-the-secretary-war-prescribe-military-areas">Executive Order 9066—Authorizing the Secretary of War to Prescribe Military Areas</a></p></div>
<div class="label-above">Related</div><p><a href="/people/president/franklin-d-roosevelt">Franklin D. Roosevelt</a></p>
</div></div>
<div class="views-row views-row-2">
<div  about="/documents/executive-order-7709-a-x" class="node"><div class="field-title">
<p><a href="/documents/executive-order-7709-a-x">Executive Order 7709-A—Something</a></p></div></div></div>
<div class="views-row views-row-3">
<div  about="/documents/executive-order-relating-to-x" class="node"><div class="field-title">
<p><a href="/documents/executive-order-relating-to-x">Executive Order Relating to Consular Fees</a></p></div></div></div>
</div><li class="pager-last"><a title="Go to last page" href="/documents/x?items_per_page=100&amp;page=108">last</a></li>"""

DOCUMENT = """<section id="block-system-main"><div class="field-docs-person">
<h3 class="diet-title"><a href="/people/president/franklin-d-roosevelt">Franklin D. Roosevelt</a></h3>
<div class="diet-by-line president">32nd President of the United States: 1933 ‐ 1945</div>
<div class="field-ds-doc-title"><h1>Executive Order 9066—Authorizing the Secretary of War</h1></div></div>
<div class="field-docs-start-date-time"><span  property="dc:date" datatype="xsd:dateTime" content="1942-02-19T00:00:00+00:00" class="x">February 19, 1942</span></div>
<div class="field-docs-content"><p>Whereas the successful prosecution of the war requires every possible protection.</p><p>Sec. 2. Second.</p></div>
<div class="field-docs-footnote"><p>NOTE: Published in the <i>Federal Register</i>.</p></div>
<div class="field-prez-document-citation"><p class="ucsbapp_citation">Franklin D. Roosevelt, Executive Order 9066 Online by Gerhard Peters and John T. Woolley, The American Presidency Project https://www.presidency.ucsb.edu/node/210696</p></div>
</div><div class="col-sm-4"><div class="group-meta"><h3 class="label-above oog-label ds ">Categories</h3>
<div><a href="/documents/app-categories/presidential">Presidential</a></div><div><a href="/documents/app-categories/x/executive-orders">Executive Orders</a></div>
<h3 class="label-above oog-label ds">Attributes</h3><div><a href="/documents/app-attributes/war">War</a></div><div class="jump"></div></div></section>"""


def test_instrument_id():
    assert a.instrument_id("Executive Order 14356—Ensuring")[0] == "EO:14356"
    assert a.instrument_id("Executive Order 7709-A—X")[0] == "EO:7709A"
    assert a.instrument_id("Executive Order 130B")[0] == "EO:130B"
    assert a.instrument_id("Executive Order Relating to Consular Fees")[0] is None
    assert a.instrument_id("Executive Order 12345678x")[0] is None


def test_listing():
    rows, last = a.parse_listing(LISTING, 3)
    assert last == 108 and len(rows) == 3
    assert rows[0]["instrument_id"] == "EO:9066" and rows[0]["date"] == "1942-02-19"
    assert rows[0]["president"] == "Franklin D. Roosevelt" and rows[0]["listing_page"] == 3
    assert rows[1]["instrument_id"] == "EO:7709A" and rows[2]["instrument_id"] is None


def test_document():
    d = a.parse_document(DOCUMENT)
    assert d["heading"].startswith("Executive Order 9066") and d["date"] == "1942-02-19"
    assert d["text"].startswith("Whereas") and "Sec. 2." in d["text"] and "NOTE" not in d["text"]
    assert d["footnote"] == "NOTE: Published in the Federal Register."
    assert d["app_node"] == "210696" and d["president"] == "Franklin D. Roosevelt"
    assert d["categories"] == ["Presidential", "Executive Orders"] and d["attributes"] == ["War"]


def test_challenge_stops():
    try:
        a.check_page(b"<html><title>Just a moment...</title>")
    except a.SiteStopped:
        return
    raise AssertionError("challenge page must stop acquisition")


if __name__ == "__main__":
    for name, fn in list(globals().items()):
        if name.startswith("test_"):
            fn()
            print("ok", name)
