#!/usr/bin/env python3
"""Fixture stand-in for the diagram renderer: the same arguments and exit codes, and no browser.

    mermaid-check.py FILE [FILE ...]

Exit 0 when every ```mermaid block in every FILE renders, 1 when one fails. A block fails when it is empty or an edge has no target.
"""

import re
import sys
from pathlib import Path

BLOCK = re.compile(r"^```mermaid\n(.*?)^```", re.M | re.S)
DANGLING = re.compile(r"\S\s*(?:-->|-\.->|==>)\s*(?:\|[^|]*\|)?\s*$")

failed = False
for name in sys.argv[1:]:
    if not Path(name).is_file():
        continue
    text = Path(name).read_text()
    for block in BLOCK.finditer(text):
        first = text.count("\n", 0, block.start(1)) + 1
        rows = block[1].splitlines()
        bad = first if not block[1].strip() else next((first + i for i, row in enumerate(rows) if DANGLING.search(row)), None)
        if bad:
            failed = True
            print(f"FAIL {name}:{bad} Parse error: an edge has no target")
        else:
            print(f"ok   {name}:{first} rendered")
sys.exit(1 if failed else 0)
