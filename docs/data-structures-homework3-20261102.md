# Data structures courseware and homework 3

## Scope

- New course hub: `site/data-structures.html`.
- Eight source readers: `site/data-structures-ch1.html` through `ch8.html`.
- Sources: eight user-provided PDF handouts, 69 physical PDF pages, from the 2026–2027 fall Data Structures and Algorithm Foundations course. Chapter 5 excludes threaded trees; chapter 7 excludes B-trees.
- Original PDFs are unchanged; source hashes and exact names are in `site/data-structures-source-map.json`. Page images were rendered at 2400 pixels wide and encoded losslessly as WebP; decoded pixels were checked against the renderer output.
- Homework walkthrough: `site/data-structures-homework3.html`; independent answer sheet and text download use `-answers.html` and `-answers.txt`.
- Both `site/index.html` and `site/courses.html` contain the new course card. Existing course readers, progress keys, source assets, and account/sync behavior are unchanged.

## Verified course conventions

1. Circular queue: chapter 3 PDF pages 5–6. `front` points to the head; `rear` points after the tail. One slot is reserved, so 11 slots hold 10 elements. The final insertion group admits n/o/p only and leaves `(front,rear)=(4,3)`.
2. Expression: chapter 3 PDF page 3. NS stores operands/intermediate results; OS starts with `#`. The final result leaves NS=`[T5]`, OS=`[#]`. Postfix is `A B C * D / - E F ** +`.
3. Address calculation: chapter 4 PDF page 1 presents both row-major and column-major formulas. The supplied addresses exclude positive-dimension row-major storage; column-major yields m=6, base=1102, target=1120. The column count is not determined beyond n≥4 for the target to exist.
4. Sparse matrices: chapter 4 PDF page 4 uses one-based triples, `data[0]` unused, and `num`/`cpot` row vectors. The empty fourth row of A has num=0 and cpot=7, not 0. A has 8 nonzeros; B has 17.

## Validation

- Run `python3 tests/data-structures-homework3.test.py` for all new local links/anchors, exact PDF hashes, source coverage, SVG XML, queue states, all 18 double-stack states, address inference, and matrix reconstruction.
- Also run `node --check site/data-structures-reader.js` and `node --check site/data-structures-homework.js`.
- Source reader navigation uses physical-page hash anchors, retains Back/Forward behavior, provides bounded zoom in a scrollable region, and remains readable without JavaScript.
- Answer-sheet printing is browser-local and does not submit anything. Text download is an alternative for copying into a course form.
- Neither private browser screenshots, student identifiers, Library identities, local paths, nor personal study progress are included in published assets.
- This repository does not submit to the university/course platform. Publishing to GitHub Pages only stores the materials and answers on the user's existing public learning website.
