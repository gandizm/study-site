"""Textbook vector notation: unchanged source, normalized TeX, and actual SVG accents.

Uses only Python's standard library. Run after the static page is assembled/built.
"""
from pathlib import Path
from html import unescape
import hashlib
import re
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
SOURCE_BLOBS = {
    'q251.md': '97d9f861738744d63cf2b2e5fbc7d3f56e5bb292',
    'q363.md': '2fa7e64d4fffea79f1a753fc652287a6577051b4',
}
FORMULA = re.compile(r'\\\[([\s\S]*?)\\\]|\$\$([\s\S]*?)\$\$|\\\(([\s\S]*?)\\\)|(?<!\\)\$([^$\n]+?)(?<!\\)\$')
OLD_VECTOR = re.compile(r'\\(?:mathbf|boldsymbol)\s*(\\[A-Za-z]+|[A-Za-z0-9])')


def normalized(source):
    """Independent compatibility oracle; never edits the authored source."""
    source = re.sub(r'\\hat\{\\(?:mathbf|boldsymbol)\s*([^}]+)\}',
                    lambda m: r'\emunit{' + m[1] + '}', source)
    source = re.sub(r'\\mathrm\s+d\\mathbf\s*([lA])',
                    lambda m: r'\emvec{\mathrm d ' + m[1] + '}', source)
    source = re.sub(r'\\mathbf\s*(\\[A-Za-z]+|[A-Za-z0-9])',
                    lambda m: ('\\emunit{' if m[1] == 'n' else '\\emvec{') + m[1] + '}', source)
    return source


original = []
for name, expected_blob in SOURCE_BLOBS.items():
    data = (ROOT / 'docs/em-energy-wedge' / name).read_bytes()
    actual_blob = hashlib.sha1(b'blob ' + str(len(data)).encode() + b'\0' + data).hexdigest()
    assert actual_blob == expected_blob, f'Authored problem source was modified: {name}'
    original.extend(next(g for g in match.groups() if g is not None).strip()
                    for match in FORMULA.finditer(data.decode()))
assert len(original) == 354
assert sum(len(OLD_VECTOR.findall(s)) for s in original) == 148

page = (ROOT / 'site/em-energy-wedge-homework.html').read_text()
rendered = list(re.finditer(r'<(span|div) class="hw-math\b[^>]*data-tex="([^"]*)"[^>]*>(.*?)</\1>', page, re.S))
assert len(rendered) == 354, 'All 354 inline, displayed, folded, and table formulas must render'
bar_total = hat_total = normal_hats = differential_bars = scalar_count = 0

for index, (old, match) in enumerate(zip(original, rendered)):
    source, markup = unescape(match[2]), match[3]
    expected = normalized(old)
    # Whitespace around the upright differential is typographically immaterial.
    equivalent = lambda s: re.sub(r'\\mathrm\s+d\s+([lA])', r'\\mathrm d\1', s)
    assert equivalent(source) == equivalent(expected), f'Unexpected source change at formula {index}: {source}'
    assert not re.search(r'\\(?:mathbf|boldsymbol)\b', source), f'Legacy bold TeX survived at {index}'
    aria = re.search(r'aria-label="([^"]*)"', match[0]).group(1)
    assert unescape(aria) == source, f'Accessible formula differs at {index}'
    assert 'data-mml-node="merror"' not in markup
    # Stretchy accents contain nested SVGs: take the complete outer SVG.
    svg_match = re.search(r'<svg\b.*</svg>', markup, re.S)
    assert svg_match, f'Missing rendered SVG at {index}'
    svg = ET.fromstring(svg_match[0])
    paths = [int(e.attrib['data-c'], 16) for e in svg.iter() if 'data-c' in e.attrib]
    bold_ranges = ((0x1D400, 0x1D433), (0x1D468, 0x1D49B),
                   (0x1D6A8, 0x1D6E1), (0x1D71C, 0x1D755), (0x1D7CE, 0x1D7D7))
    assert not any(lo <= cp <= hi for cp in paths for lo, hi in bold_ranges), f'Bold glyph remains at {index}'
    bars = hats = 0
    for mover in svg.iter():
        if mover.get('data-mml-node') != 'mover' or len(mover) < 2:
            continue
        base, accent = mover[0], mover[-1]
        codes = {int(e.attrib['data-c'], 16) for e in accent.iter() if 'data-c' in e.attrib}
        base_codes = [int(e.attrib['data-c'], 16) for e in base.iter() if 'data-c' in e.attrib]
        is_bar = bool(codes & {0xAF, 0x2013, 0x203E}) or (accent.get('data-mml-node') == 'mo' and any(e.tag.endswith('rect') for e in accent.iter()))
        is_hat = bool(codes & {0x5E, 0x2C6})
        if is_bar:
            bars += 1
            if base_codes in ([0x64, 0x1D459], [0x64, 0x1D434]):
                differential_bars += 1
        if is_hat:
            hats += 1
            if base_codes == [0x1D45B]:
                normal_hats += 1
    assert bars == expected.count(r'\emvec{'), f'Incorrect vector overlines at {index}: {bars} vs {expected}'
    assert hats == expected.count(r'\emunit{'), f'Incorrect unit hats at {index}: {hats} vs {expected}'
    if not OLD_VECTOR.search(old):
        assert source == old, f'A scalar-only formula changed at {index}'
        scalar_count += 1
    bar_total += bars
    hat_total += hats

assert (bar_total, hat_total, normal_hats, differential_bars) == (107, 41, 10, 2), (bar_total, hat_total, normal_hats, differential_bars)
for name in ('energy-flow.svg', 'image-charges.svg'):
    diagram = ET.parse(ROOT / 'site/assets/em-energy-wedge' / name)
    labels = [''.join(e.itertext()) for e in diagram.iter() if e.tag.endswith('text')]
    assert not any(re.search(r'\\(?:mathbf|boldsymbol|hat)|[\U0001d400-\U0001d433]', label) for label in labels)
print(f'PASS: unchanged authored sources; 354 complete formulas; 107 vector bars, 41 unit hats (10 outward normals), 2 whole differential bars; {scalar_count} scalar-only formulas unchanged; no bold math glyphs or missed diagram labels.')
