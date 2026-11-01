# Closed-surface integral rendering repair (2026-11-01)

## Scope and cause

`site/em-ch2-homework.html` contained six pre-rendered MathJax SVG expressions
with seven `\oiint` commands. The earlier renderer silently emitted a red
literal command instead of a closed double integral; there was no `merror`
node, so merely counting rendered formulas or checking `merror` missed it.

Only the six formula interiors were regenerated with MathJax 4.1.0 and its
New Computer Modern font. Each closed surface integral is a native U+222F
vector path, not an ordinary double integral or a font-dependent Unicode
text fallback. `\iiint` remains the distinct triple volume integral.
All six outer wrappers, accessible labels, TeX sources and all non-target
page bytes remain unchanged. No runtime dependency, CSS, course content,
progress key, learning record, original slide, or image was changed.

The existing PPT2 P12/P19/P20 links were independently visually checked.
Their PDF-derived SVG renderer does not share this undefined-command bug;
healthy PPT formulas and original notation were therefore left untouched.

## Rebuild

Run from the repository root with Node 24 (only needed to regenerate SVGs):

```sh
npm install --prefix /tmp/study-em-math --no-audit --no-fund \
  @mathjax/src@4.1.0 @mathjax/mathjax-newcm-font@4.1.0
NODE_PATH=/tmp/study-em-math/node_modules node scripts/render-em-closed-integrals.cjs
python3 tests/em-closed-integrals.test.py
```

The generator fails on undefined-command or font-text fallback and on an
unexpected expression count. It embeds paths directly, avoiding glyph-ID
collisions with the existing SVGs. The source remains in `data-tex`.
The Python regression requires no extra dependencies and runs in Pages CI.
It fails against the previous page and passes the repaired page, including
formulas inside initially collapsed details.

## Validation

- Exact byte comparison outside the six intended SVG replacements; all TeX
  and accessible labels preserved. Independent reviewer confirmed 7 closed
  double glyphs and 4 unchanged triple-volume glyphs within affected formulas.
- All existing deployment validators and mathematical/progress tests passed.
- Real cloud Chromium preview: desktop and 390px/320px fixed-width CSS iframes,
  all 17 details opened. All 473 formulas retained, 7 native U+222F paths,
  zero red command fallbacks. No document-wide horizontal overflow; long
  formulas scroll locally and the boxed result's right edge is reachable.
- The narrow viewport check is not a physical phone or touch/DPR test.

Screenshots and diagnostic logs are retained privately, not published here.
Deployment and live-page checks are reported separately after publication.
