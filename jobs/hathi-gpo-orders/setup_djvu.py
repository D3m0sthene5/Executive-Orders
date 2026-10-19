"""Unpack checksum-pinned MSYS2 decoder tools privately; no system installation."""
import hashlib
import html
import json
from pathlib import Path
import re
import subprocess
from routes_net import HERE, RouteNetwork


def main():
    net = RouteNetwork()
    dest = (HERE / ".cache/djvu").resolve()
    assert dest.is_relative_to(HERE.resolve())
    dest.mkdir(parents=True, exist_ok=True)
    records = []
    for name in ("djvulibre", "cc-libs", "libgcc", "libstdc++", "libwinpthread", "libiconv", "libjpeg-turbo", "zlib"):
        page = "https://packages.msys2.org/packages/mingw-w64-ucrt-x86_64-" + name
        r = net.fetch("decoder_dependency", page)
        text = r["body"].decode()
        links = re.findall(r'https://mirror\.msys2\.org/mingw/ucrt64/[^"<> ]+\.pkg\.tar\.zst', text)
        if not links:
            raise ValueError("No official binary package for " + name)
        # MSYS2 documents this primary server separately from its geo selector:
        # https://www.msys2.org/dev/mirrors/ . Its own robots rules still apply.
        download = html.unescape(links[0]).replace("https://mirror.msys2.org/", "https://repo.msys2.org/")
        plain = re.sub(r"<[^>]+>", " ", html.unescape(text))
        hashes = re.findall(r"\b[a-f0-9]{64}\b", plain)
        if not hashes:
            raise ValueError("No published SHA-256 for " + name)
        result = net.fetch("decoder_dependency", download)
        actual = hashlib.sha256(result["body"]).hexdigest()
        assert actual in hashes, (name, actual)
        archive = dest / download.rsplit("/", 1)[-1]
        archive.write_bytes(result["body"])
        listing = subprocess.check_output(["tar", "-tf", str(archive)], text=True).splitlines()
        assert all(not p.startswith(("/", "\\")) and ".." not in p.split("/") for p in listing)
        if any(p.startswith("ucrt64/bin/") for p in listing):
            subprocess.run(["tar", "-xf", str(archive), "-C", str(dest), "ucrt64/bin"], check=True)
        records.append({"name": name, "metadata_url": page, "download_url": download, "sha256": actual})
        print(name, "verified and unpacked", flush=True)
    (HERE / "output/DECODER.json").write_text(json.dumps(records, indent=2) + "\n")
    exe = dest / "ucrt64/bin/djvutxt.exe"
    result = subprocess.run([str(exe), "--help"], capture_output=True, text=True)
    print("decoder_exit", result.returncode, (result.stderr + result.stdout)[:1000])


if __name__ == "__main__":
    main()
