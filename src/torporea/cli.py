from __future__ import annotations

import argparse
import sys

from . import __version__
from .detect import scan


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="2rporea", description="Detect and convert projects to RPoRea (RPoem + Reaxt).")
    ap.add_argument("--version", action="version", version=__version__)
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("scan", help="list the backend and frontend frameworks found in a directory")
    s.add_argument("path")
    a = ap.parse_args(argv)
    if a.cmd == "scan":
        found = scan(a.path)
        if not found:
            print("nothing recognised")
            return 1
        for f in found:
            print(f"{f.kind:8} {f.framework:8} ({f.language})  e.g. {', '.join(f.evidence[:2])}")
        return 0
    return 2


if __name__ == "__main__":
    sys.exit(main())
