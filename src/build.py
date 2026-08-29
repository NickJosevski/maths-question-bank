#!/usr/bin/env python3
"""Build the app from the shell and the exported data.

  src/build.py             both variants (default)
  src/build.py --inline    only the single self-contained file
  src/build.py --lazy      only the split build

Reads src/, writes the repo root - which is what GitHub Pages serves.

Two variants, from ONE shell so they cannot drift apart:

  index.html                the site. Questions inline, each year's working
                            pulled in on first use from working-yr{7,8,9,10}.js.
                            About a third of the size to open.
  maths-question-bank.html  every chain built in. One file, nothing to fetch,
                            works anywhere - including from a phone's Files app
                            with no network. This is the fallback, and the thing
                            to download if you want the bank offline.

The lazy build injects chunks as <script> tags rather than fetching them: a
fetch() from a file:// page is blocked by CORS, so a fetch-based design would
fail in exactly the case that matters - the file opened straight off a device.
The chunks must sit beside the HTML.

Two things here are load-bearing:

1. The bank is injected with every '<' escaped as \\u003c, so a question
   containing markup cannot terminate the <script> tag early. JSON.parse
   restores the real characters.
2. The output is a COMPLETE document with <meta charset="utf-8"> first in head.
   The questions are full of real Unicode - minus signs, surds, degrees - and
   without a declared charset the browser sniffs and can get it wrong: U+2212
   rendered as mojibake in testing, silently corrupting the maths.
"""
import json, sys, pathlib

SRC = pathlib.Path(__file__).resolve().parent    # inputs
OUT = SRC.parent                                 # repo root == what Pages serves
shell = (SRC / "app_shell.html").read_text(encoding="utf-8")
main = json.loads((SRC / "questions.json").read_text(encoding="utf-8"))

# The two earlier Year 7 test papers are exported separately upstream, because
# their questions carry tables and answer boxes that the chapter notation cannot
# express. Merge them in here.
extra_path = SRC / "extra.json"
if extra_path.exists():
    extra = json.loads(extra_path.read_text(encoding="utf-8"))
    have = {(c["y"], c["n"]) for c in main["chapters"]}
    main["questions"] += extra["questions"]
    main["chapters"] += [c for c in extra["chapters"] if (c["y"], c["n"]) not in have]
    main["chapters"].sort(key=lambda c: (int(c["y"]), c["n"]))
    ids = [q["id"] for q in main["questions"]]
    assert len(ids) == len(set(ids)), "duplicate question ids after merge"
    print(f"  merged extra    : {len(extra['questions'])} questions, "
          f"{len(extra['chapters'])} chapters")

# Step-by-step working lives in its own file so that regenerating questions.json
# upstream cannot clobber it.
work_path = SRC / "working.json"
work = json.loads(work_path.read_text(encoding="utf-8")) if work_path.exists() else {}
ids = {q["id"] for q in main["questions"]}
orphan = [k for k in work if k not in ids]
if orphan:
    print(f"  WARNING: {len(orphan)} chains match no question: {orphan[:8]}")
work = {k: v for k, v in work.items() if k in ids}
year_of = {q["id"]: q["y"] for q in main["questions"]}

# id -> step count. Always inline, ~11 KB, so the app knows which questions have
# a chain before any chunk has loaded.
workidx = {k: len(v["w"]) for k, v in work.items()}

bank = json.dumps(main, ensure_ascii=False, separators=(",", ":"))
if "__BANK__" not in shell:
    sys.exit("shell has no __BANK__ placeholder")


def esc(txt):
    out = txt.replace("<", "\\u003c")
    assert "</script" not in out.lower(), "escaping failed"
    return out


safe = esc(bank)

# split the shell into head-ish (metas/title/link/style) and body at </style>
if "</style>" not in shell:
    sys.exit("shell has no </style> to split on")
head, body_tpl = shell.split("</style>", 1)
head += "</style>"


def build(out, lazy):
    body = (body_tpl
            .replace("__BANK__", safe)
            .replace("__WORKIDX__", esc(json.dumps(workidx, separators=(",", ":"))))
            .replace("__WORK__", "{}" if lazy
                     else esc(json.dumps(work, ensure_ascii=False, separators=(",", ":"))))
            .replace("__LAZY__", "true" if lazy else "false"))
    for ph in ("__BANK__", "__WORKIDX__", "__WORK__", "__LAZY__"):
        assert ph not in body, f"{ph} not substituted"
    doc = ("<!doctype html>\n<html lang=\"en-AU\">\n<head>\n" + head
           + "\n</head>\n<body>\n" + body + "\n</body>\n</html>\n")
    out.write_text(doc, encoding="utf-8")

    # the charset must land in head, before any non-ASCII byte
    raw = out.read_bytes()
    cs = raw.find(b'<meta charset="utf-8">')
    first_hi = next((i for i, b in enumerate(raw) if b > 127), len(raw))
    assert cs != -1, "charset meta missing"
    assert cs < first_hi, "charset meta appears after the first non-ASCII byte"
    assert cs < 1024, "charset meta not within the first 1024 bytes"
    return out.stat().st_size / 1024


want = [a for a in sys.argv[1:] if a.startswith("--")] or ["--inline", "--lazy"]

if "--inline" in want:
    kb = build(OUT / "maths-question-bank.html", lazy=False)
    print(f"  inline : maths-question-bank.html   {kb:>6.0f} KB"
          f"   ({len(work)} chains built in)")

if "--lazy" in want:
    kb = build(OUT / "index.html", lazy=True)
    chunks = {}
    for qid, rec in work.items():
        chunks.setdefault(year_of[qid], {})[qid] = rec
    # drop stale chunks so a removed year cannot linger and load wrong data
    for old in OUT.glob("working-yr*.js"):
        if old.stem.replace("working-yr", "") not in chunks:
            old.unlink()
            print(f"  removed stale chunk {old.name}")
    total = 0
    for y in sorted(chunks, key=lambda v: int(v)):
        payload = json.dumps(chunks[y], ensure_ascii=False, separators=(",", ":"))
        js = ("window.__mqbWork = window.__mqbWork || {};\n"
              "Object.assign(window.__mqbWork, " + payload + ");\n")
        p = OUT / f"working-yr{y}.js"
        p.write_text(js, encoding="utf-8")
        total += p.stat().st_size / 1024
        print(f"           working-yr{y}.js{' ' * (17 - len(y))}{p.stat().st_size/1024:>6.0f} KB"
              f"   ({len(chunks[y])} chains)")
    print(f"  lazy   : index.html                {kb:>6.0f} KB"
          f"   + {total:.0f} KB in {len(chunks)} chunks, loaded on demand")

print(f"  questions: {len(main['questions'])}   chapters: {len(main['chapters'])}"
      f"   chains: {len(work)}")
