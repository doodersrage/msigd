#!/usr/bin/env python3
"""Read-only probe for MSI monitors speaking the msigd HID protocol.

Sends only "58<code>" (read) commands. Any other command is refused, so this
cannot change monitor settings. Codes default to every setting code found in
src/msigd.cpp; pass codes on the command line to probe specific ones.

  tools/probe_reads.py [--dev /dev/hidrawN] [--json out.json] [--diff base.json] [code ...]
"""
import argparse
import json
import os
import re
import select
import sys
from pathlib import Path

PACKET = 64
SRC = Path(__file__).resolve().parent.parent / "src" / "msigd.cpp"


def known_codes():
    text = SRC.read_text(errors="replace")
    names = {}
    for code, name in re.findall(r'"(00[0-9a-f:;<=>?]{2,3})",\s*"([a-z_0-9]+)"', text):
        names.setdefault(code, set()).add(name)
    return {c: sorted(n) for c, n in sorted(names.items())}


class Monitor:
    def __init__(self, dev):
        self.fd = os.open(dev, os.O_RDWR)
        self.drain()

    def drain(self):
        while select.select([self.fd], [], [], 0.05)[0]:
            os.read(self.fd, PACKET)

    def read_setting(self, code, timeout=1.0):
        cmd = "58" + code
        if not re.fullmatch(r"58[0-9a-f:;<=>?]{4,5}", cmd):
            raise ValueError(f"refusing non-read command {cmd!r}")
        pkt = b"\x01" + cmd.encode() + b"\r"
        os.write(self.fd, pkt + b"\0" * (PACKET - len(pkt)))
        if not select.select([self.fd], [], [], timeout)[0]:
            return None, b""
        raw = os.read(self.fd, PACKET)
        body = raw[1:].split(b"\r", 1)[0]
        return body.decode("latin-1").replace("\0", "_"), raw


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dev", default="/dev/hidraw4")
    ap.add_argument("--json")
    ap.add_argument("--diff", help="baseline JSON; print only codes whose value changed")
    ap.add_argument("codes", nargs="*")
    a = ap.parse_args()

    names = known_codes()
    codes = a.codes or list(names)
    mon = Monitor(a.dev)
    base = json.loads(Path(a.diff).read_text()) if a.diff else None
    results = {}
    for code in codes:
        ret, raw = mon.read_setting(code)
        label = ",".join(names.get(code, ["?"]))
        if ret is None:
            status, val = "timeout", ""
        elif ret.startswith("5b" + code):
            status, val = "ok", ret[len("5b" + code):]
        elif ret.startswith("56006"):
            status, val = "unsupported", ret
        else:
            status, val = "other", ret
        results[code] = {"names": names.get(code, []), "status": status,
                         "value": val, "raw": raw.hex()}
        if base is None:
            print(f"{code:6} {status:11} {val!r:24} {label}")
        elif code in base and base[code]["value"] != val:
            print(f"{code:6} {base[code]['value']!r:>8} -> {val!r:8} {label}")
        mon.drain()
    if a.json:
        Path(a.json).write_text(json.dumps(results, indent=1))


if __name__ == "__main__":
    sys.exit(main())
