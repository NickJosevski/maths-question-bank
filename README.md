# Maths Question Bank

A self-marking practice app over **1,346 maths questions** for the Australian
curriculum, Years 7–10 — 73 chapters, with a full step-by-step working chain on
803 of them. No backend, no database, no accounts, no tracking. It is a static
page; progress lives in your own browser.

**→ https://nickjosevski.github.io/maths-question-bank/**

## Modes

| Mode | What it does |
|---|---|
| **Practice** | Pick a year and chapter, step through its questions in order (easiest first). Reveal the answer, mark yourself. |
| **Mixed drill** | Questions drawn at random across chapters, filtered by year and difficulty. Interleaved practice, closer to what an exam actually does than working one chapter at a time. |
| **Weak spots** | Per-chapter accuracy, weakest first, plus a queue that re-serves every question you missed last time, oldest first. |
| **Exam** | Generates a fresh mixed paper to a target mark count and difficulty profile, runs a clock, then marks question by question (full / half / none) and reports a score broken down by chapter. |

Keyboard, in the one-question-at-a-time modes: `space` reveals, `1` = got it,
`2` = missed it, `←` / `→` move between questions.

Progress is kept in `localStorage` under `mathsqb.v1`, **on that device only**.
Nothing is uploaded and nothing is shared between devices or browsers. "Clear all
progress" on the Weak spots tab wipes it.

## Step-by-step working

Questions where a derivation helps carry a full working chain under the answer,
behind a "Show full working" toggle. Each line is one manipulation paired with
the reason it happened — so expanding brackets and collecting like terms are
separate lines, sign work gets its own line, and equation questions finish by
substituting the answer back into both sides. Chains average about 19 steps.

Not every question has one. Chains exist only where there is a procedure to
show; pure recall, naming and "explain why" questions are deliberately left
without, since their answer already *is* the reasoning.

## Take it offline

`maths-question-bank.html` is the whole thing — every question, answer and
working chain — in **one 3.9 MB file**. Save it, AirDrop it, put it in a phone's
Files app: it works with no network at all. That is the fallback build, and it is
the one to reach for if anything about the hosted version misbehaves.

## Two builds, one source

| File | Size to open | Notes |
|---|---|---|
| `index.html` | **1.7 MB** | What the site serves. Questions inline; each year's working pulled in on first use from `working-yr7.js` … `working-yr10.js` (239–754 KB each). |
| `maths-question-bank.html` | **3.9 MB** | Everything built in. One file, nothing to fetch, works anywhere. |

A Year 7 student on the hosted build downloads 1.7 MB + 239 KB instead of 3.9 MB.
Both come out of the same `src/app_shell.html`, so they cannot drift apart — the
only difference is whether the chains are inlined or split out.

The lazy build injects chunks as `<script>` tags rather than fetching them,
because `fetch()` from a `file://` page is blocked by CORS: a fetch-based design
would fail in exactly the case that matters most, the file opened straight off a
device. If a chunk is missing the app still works for questions and answers, and
the working panel says so and names the single-file version.

## Building

```sh
python3 src/build.py            # both builds
python3 src/build.py --inline   # just the offline single file
python3 src/build.py --lazy     # just the site
```

No dependencies — standard-library Python 3. `src/app_shell.html` is the
editable source; `index.html` and `maths-question-bank.html` are generated and
should never be edited by hand.

| Path | What |
|---|---|
| `src/app_shell.html` | The app: markup, stylesheet, and all of its JavaScript. |
| `src/questions.json` | The bank — every question and answer, pre-rendered. |
| `src/extra.json` | Two earlier Year 7 test papers, exported separately. |
| `src/working.json` | The step-by-step chains, keyed by question id. |
| `src/build.py` | Merges those into the two builds. |
| `src/sync.sh` | Re-pulls the three JSONs from the generator repo, then builds. |

The three JSON files are **generated upstream**, by a separate private repo that
reads the textbook chapters and writes the bank out. This repo owns the app; that
one owns the data.

## Two things in the build that are load-bearing

**Notation is rendered in Python, never in JavaScript.** The upstream exporter
pushes every question through one hardened `render_math`, and the app only ever
inserts already-rendered HTML — it never parses fraction macros or escapes tags.
That renderer is gated by its own checker and has survived several rounds of
silent-corruption bugs; a JavaScript reimplementation would mean a fresh
generation of them. If you extend this app, keep that boundary.

**The output declares its charset.** The questions are full of real Unicode —
`−`, `√`, `°`, `≤`, `π`. Built without `<meta charset="utf-8">` first in head the
browser sniffs the encoding and can get it wrong: in testing `5a(2a − 3)`
rendered as `5a(2a β ′ 3)`, silently corrupting the maths on screen. `build.py`
asserts the charset meta lands in the first 1024 bytes and before the first
non-ASCII byte.

A third, smaller one: the bank is injected with every `<` escaped as the JSON escape `\u003c`, so
a question containing markup cannot terminate the `<script>` tag early.

## A CSS trap worth remembering

Components here set `display: flex`, which is an author rule and therefore beats
the UA stylesheet's `[hidden] { display: none }`. Setting `hidden` on a flex
component silently does nothing. The stylesheet carries an explicit
`[hidden] { display: none !important; }` to fix it — don't remove it.

## Provenance

The questions were written fresh, in the style of the exercises in *ICE-EM
Mathematics* (3rd edition, Years 7–10), by working through those chapters; the
chapter titles and numbering follow that series. Every answer was re-derived from
scratch by an independent pass that never saw the answer key, with disagreements
ruled on by a third pass.

*ICE-EM Mathematics* is © Cambridge University Press / the University of
Melbourne. Nothing from the books themselves is reproduced or redistributed here.

## Licence

Split deliberately, because the two halves of this repo are not the same thing.

**The code is MIT.** `src/app_shell.html`, `src/build.py` and `src/sync.sh` —
take them, build your own question bank over your own content.

**The question content is not licensed.** `src/questions.json`, `src/extra.json`
and `src/working.json`, and the generated files that embed them (`index.html`,
`maths-question-bank.html`, `working-yr*.js`) — all rights reserved, for the
provenance reasons above. Those generated files are MIT only as to the app code
they carry.

Full text and scope in [LICENSE](LICENSE).
