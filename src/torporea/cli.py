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
    c = sub.add_parser("convert", help="convert backends to RPoem via 2Poem / Java_to / COBOL_to; list the rest in MIGRATION.md")
    c.add_argument("path")
    c.add_argument("-o", "--output", default=None)
    c.add_argument("--rpoem-path", default="../RPoem")
    c.add_argument("--dry-run", action="store_true")
    a = ap.parse_args(argv)
    if a.cmd == "convert":
        import os
        from .convert import run
        return run(a.path, a.output or a.path.rstrip("/\\") + "-rporea", a.rpoem_path, a.dry_run)
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
