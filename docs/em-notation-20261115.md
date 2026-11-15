# Electromagnetics notation correction

Scope: only homework 2.5-1 and 3.6-3. Both original Markdown sources and all
original textbook crops remain byte-identical. No other course is edited.

`scripts/em-textbook-notation.cjs` owns the two typography definitions:

```latex
\def\emvec#1{\overline{#1}}
\def\emunit#1{\hat{#1}}
```

The shared renderer adapts the legacy bold notation without rewriting answers:
ordinary vectors receive a bar; unit vectors receive only a hat, without bold;
the outward unit normal receives a hat; directed line/surface differentials
receive a bar over the complete differential. Scalar magnitudes and components
are unchanged. All 354 formulas, including folded explanations and tables, are
regenerated to static SVG. Only the five compressed HTML parts and their manifest
change; existing image objects are reused.

Textbook evidence: Zhong Shunshi, Electromagnetic Fields and Waves, 2nd edition,
printed pp. 3-4 (notation), 57 (power densities), 59 (Example 2.5-3), 62 (2.5-1),
89-90 (grounded wedge and five images), 104 (3.6-3).

Independent physics review confirms the existing field directions, energy
balance, image locations/signs and numerical potential. The dimensionless
potential sum is 0.3200314700267503; the vacuum potential is about 129.433 V,
or 129.613 V with the textbook approximation 9e9. This correction changes
notation, not these results.

The notation regression test checks every rendered formula and preserves the
original source hashes. Existing integrity, mathematical and UI tests still run
in the full Pages workflow. Publication remains the existing small-object
assembly flow; no multi-megabyte Git object is uploaded.
