# Week 10–11 electromagnetics homework

Six exercises from Zhong Shunshi, Electromagnetic Fields and Waves, 2nd edition (2015), ISBN 9787302389484. Sources were inspected in the supplied textbook: printed 104–105 (PDF 121–122), printed 161–162 (PDF 178–179). RMS phasors follow printed 133 (PDF 150), equations 5.3-5 and 5.3-6. The public pages contain paraphrased conditions, original solutions and two original SVG diagrams, not textbook scans.

## Editorial checks

- 3.7-2: triangular potential is on x=a; its peak is U0/2.
- 3.7-3: top boundary is zero normal derivative, not zero potential; bottom-wall charge uses the conductor-to-air +y normal.
- 5.1-4: coefficient in (a) is 3; sin(theta) belongs inside the exponent in (d).
- 5.2-1: the sought magnetic field is the same-frequency field, with no added static field; time-averaged peak-amplitude power carries 1/2.
- 5.3-2: complex power is Udot Idot*/2; real average power is its real part. No unstated in-phase assumption.
- 5.3-4: subscript e is RMS. The requested phasors have no sqrt(2); their cross product has no 1/2. The instantaneous power oscillates at 2 omega.

The six sources were independently reviewed. The renderer reuses the established short vector rule, pointed unit-direction hats and full directed-differential rule in scripts/em-textbook-notation.cjs. A phasor dot stays above the vector bar and scalar U/I have no bar.

## Rebuild

Use mathjax-full@3.2.2 and marked@16.4.2 via NODE_PATH, then run:

    node scripts/build-em-week1011.cjs
    python3 scripts/assemble-em-week1011.py --pack
    python3 tests/em-week1011-parts.test.py
    python3 scripts/assemble-em-week1011.py
    python3 scripts/assemble-em-energy-wedge.py
    python3 scripts/build-study-navigation.py
    python3 tests/em-week1011.test.py
    node tests/em-week1011-ui.test.cjs
    python3 tests/study-navigation.test.py

Commit reviewed compressed parts, not reconstructed HTML. The publication workflow uses only standard Python/Node to verify and reconstruct frozen assets. The two pages contain 375 and 84 static SVG formula occurrences; 24 teaching folds are closed by default. All existing workflow tests were run against the changed build. The homepage uses the first-publication date and optional same-day timestamp; editing an old assignment must not change those fields.

Local browser QA covered the 390px viewport (no body overflow), desktop formula rendering and diagrams, all-fold expand/collapse, six-question copy context, dismissal/refocus and the RMS phasor notation. No learning progress or LMS submission was changed.
