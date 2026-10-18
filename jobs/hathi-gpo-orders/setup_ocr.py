"""Private Windows OCR dependency from the tesserocr project's recommended builds."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tarfile
import io
from routes_net import HERE, RouteNetwork


def main():
    net = RouteNetwork()
    dest = HERE / ".cache/ocr"
    dest.mkdir(parents=True, exist_ok=True)
    # This channel is explicitly recommended by the tesserocr project.
    url = "https://conda.anaconda.org/simonflueckiger/win-64/tesserocr-2.11.0-py312_tesseract_5.5.3_0.tar.bz2"
    package = net.fetch("ocr_dependency", url)
    digest = hashlib.sha256(package["body"]).hexdigest()
    assert digest == "4f6126124088052be9dc9283d79cec6d685f78c561d1dbd6d3d1978ed292e990"
    with tarfile.open(fileobj=io.BytesIO(package["body"]), mode="r:bz2") as archive:
        for member in archive.getmembers():
            if member.isfile() and member.name.startswith("Lib/site-packages/"):
                relative = Path(member.name.removeprefix("Lib/site-packages/"))
                target = (dest / "python" / relative).resolve()
                assert target.is_relative_to((dest / "python").resolve())
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(archive.extractfile(member).read())
    model_url = "https://raw.githubusercontent.com/tesseract-ocr/tessdata_fast/4.1.0/eng.traineddata"
    model = net.fetch("ocr_dependency", model_url)
    (dest / "tessdata").mkdir(exist_ok=True)
    (dest / "tessdata/eng.traineddata").write_bytes(model["body"])
    sys.path.insert(0, str(dest / "python"))
    import tesserocr
    info = {"recommendation": "https://pypi.org/project/tesserocr/#windows", "package_url": url, "package_sha256": digest,
            "model_url": model_url, "model_sha256": model["sha256"], "version": tesserocr.tesseract_version()}
    (HERE / "output/OCR_ENGINE.json").write_text(json.dumps(info, indent=2) + "\n")
    print(info["version"])
    with tesserocr.PyTessBaseAPI(path=str(dest / "tessdata"), lang="eng") as api:
        api.SetImageFile(str(HERE / ".cache/commons_page_7.pgm"))
        print(api.GetUTF8Text())


if __name__ == "__main__":
    main()
