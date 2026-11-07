"""Validate the draft Zenodo and CITATION.cff metadata.

Run with the venv at C:/Users/danie/eo-venvs/zen (cffconvert, jsonschema, PyYAML):
  C:/Users/danie/eo-venvs/zen/Scripts/python.exe -I validate_metadata.py

Checks (1) .zenodo.json against the local schema, (2) CITATION.cff with cffconvert (CFF schema 1.2.0),
(3) that the two files agree on title, version, first author and licence.
"""
import json
import os
import subprocess
import sys

import jsonschema

here = os.path.dirname(os.path.abspath(__file__))
zj = json.load(open(os.path.join(here, ".zenodo.json"), encoding="utf-8"))
schema = json.load(open(os.path.join(here, "zenodo_metadata.schema.json"), encoding="utf-8"))
jsonschema.Draft7Validator(schema).validate(zj)
print(".zenodo.json: valid against the local schema (%d fields)" % len(zj))

cff_exe = os.path.join(os.path.dirname(sys.executable), "cffconvert.exe")
r = subprocess.run([cff_exe, "--infile", os.path.join(here, "CITATION.cff"), "--validate"],
                   capture_output=True, text=True)
print("CITATION.cff via cffconvert:", (r.stdout + r.stderr).strip() or "ok", "(exit %d)" % r.returncode)

try:
    import yaml
except ImportError:
    print("consistency check skipped: PyYAML not installed")
else:
    cff = yaml.safe_load(open(os.path.join(here, "CITATION.cff"), encoding="utf-8"))
    assert cff["title"] == zj["title"], "title differs"
    assert cff["version"] == zj["version"], "version differs"
    assert cff["authors"][0]["family-names"] + ", " + cff["authors"][0]["given-names"] == zj["creators"][0]["name"], "author differs"
    assert cff["license"].lower() == zj["license"].lower(), "licence differs"
    print("consistency: title, version, author and licence agree in both files")
sys.exit(r.returncode)
