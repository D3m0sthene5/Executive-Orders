"""Convert CRLF to LF in place. Reads the whole file before opening it for writing; refuses to empty a file."""
import sys

for p in sys.argv[1:]:
    with open(p, "rb") as fh:
        data = fh.read()
    fixed = data.replace(b"\r\n", b"\n")
    if fixed != data:
        if data and not fixed:
            sys.exit("refusing to empty " + p)
        with open(p, "wb") as fh:
            fh.write(fixed)
    print("%s %d bytes" % (p, len(fixed)))
