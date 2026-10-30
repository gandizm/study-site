#!/usr/bin/env python3
"""Offline/CI structural checks for the public DSP course redraw.

Uses only Python's standard library and files below site/.  Source SHA256 values
are checked for metadata consistency, NOT rehashed against private PPTs.  This is
not a substitute for mathematical/semantic or browser visual review.

Run: python3 scripts/validate-dsp-course-redraw.py
     python3 scripts/validate-dsp-course-redraw.py --json-out /tmp/dsp-report.json
     python3 scripts/validate-dsp-course-redraw.py --self-test
An explicit --allow-incomplete supports staged integration; default requires all
15 sections, 14 source decks, 506 distinct physical pages, and 89 referenced SVGs.
"""
from __future__ import annotations

import argparse
import collections
from html.parser import HTMLParser
import json
import math
from pathlib import Path
import re
import struct
import sys
import tempfile
from urllib.parse import unquote, urlsplit
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
EXPECTED_FILES = (
    {f'ch1-1{i}.json' for i in range(1, 5)}
    | {f'ch2-2{i}.json' for i in range(1, 7)}
    | {f'ch3-3{i}.json' for i in range(1, 5)}
    | {'supplement-fourier.json'}
)
EXPECTED_SECTIONS, EXPECTED_DECKS, EXPECTED_PAGES, EXPECTED_SVGS = 15, 14, 506, 89
MATH_NS = 'http://www.w3.org/1998/Math/MathML'
SVG_NS = 'http://www.w3.org/2000/svg'
ARITY = dict(mfrac=2, msub=2, msup=2, munder=2, mover=2, mroot=2,
             msubsup=3, munderover=3)
MATH_TAGS = set(('math mrow mi mn mo mtext mspace mfrac msqrt mroot msup msub '
                 'msubsup munder mover munderover mtable mtr mtd mfenced mstyle '
                 'menclose semantics annotation annotation-xml mpadded mphantom').split())
HTML_TAGS = set(('p div span strong em b i u small ul ol li table thead tbody tfoot '
                 'tr th td caption h2 h3 h4 h5 h6 br hr a code pre sub sup blockquote '
                 'details summary').split()) | MATH_TAGS
VOID_TAGS = {'br', 'hr', 'mspace'}
PRIVATE = re.compile(r'(?:/(?:workspace|home|tmp|private)/|file://|sediment://|sandbox:/|'
                     r'localhost|127\.0\.0\.1|0\.0\.0\.0|\.dsp-qa(?:/|\b)|'
                     r'dsp_sources_\d+)', re.I)
MATH_BLOCK = re.compile(r'<math\b[^>]*>.*?</math\s*>', re.S | re.I)
RAW_TEX = re.compile(r'\\(?:frac|sum|int|begin|omega|mathrm|left|right|alpha|delta)\b')


def require(ok, message):
    if not ok:
        raise ValueError(message)


def local_name(tag):
    return tag.rsplit('}', 1)[-1]


def walk(value, path='$'):
    """Visit every string, including nested example/check/metadata fields."""
    if isinstance(value, str):
        yield path, value
    elif isinstance(value, dict):
        for key, child in value.items():
            yield from walk(child, f'{path}.{key}')
    elif isinstance(value, list):
        for index, child in enumerate(value):
            yield from walk(child, f'{path}[{index}]')


def page_set(value, page_count, label, allow_empty=False):
    require(isinstance(value, list), f'{label}: must be an array')
    require(allow_empty or value, f'{label}: empty page list')
    require(all(type(n) is int and 1 <= n <= page_count for n in value),
            f'{label}: page outside 1..{page_count} or not an integer')
    require(len(value) == len(set(value)), f'{label}: duplicate page number')
    return set(value)


def math_blocks(text, label):
    blocks = MATH_BLOCK.findall(text)
    require(len(blocks) == len(re.findall(r'<math\b', text, re.I)),
            f'{label}: unclosed or malformed <math> block')
    for number, source in enumerate(blocks, 1):
        try:
            root = ET.fromstring(source)
        except ET.ParseError as exc:
            raise ValueError(f'{label} math#{number}: invalid XML: {exc}') from exc
        require(root.tag == f'{{{MATH_NS}}}math',
                f'{label} math#{number}: missing/wrong MathML namespace')
        for elem in root.iter():
            tag = local_name(elem.tag)
            require(tag in MATH_TAGS and elem.tag.startswith('{'+MATH_NS+'}'),
                    f'{label} math#{number}: unsupported MathML element {elem.tag}')
            if tag in ARITY:
                require(len(elem) == ARITY[tag],
                        f'{label} math#{number}: <{tag}> needs {ARITY[tag]} children, '
                        f'found {len(elem)} ({[local_name(x.tag) for x in elem]})')
    return len(blocks)


class Fragment(HTMLParser):
    """Strict enough to catch swallowed <N text and malformed nested markup."""
    def __init__(self, label):
        super().__init__(convert_charrefs=True)
        self.label, self.stack, self.text, self.links = label, [], [], []

    def handle_starttag(self, tag, attrs):
        require(tag in HTML_TAGS, f'{self.label}: unexpected <{tag}>; escape text < as &lt;')
        names = [name for name, _ in attrs]
        require(len(names) == len(set(names)), f'{self.label}: duplicate <{tag}> attribute')
        for name, value in attrs:
            require(not name.startswith('on'), f'{self.label}: inline event handler {name}')
            if name in ('href', 'src'):
                require(bool(value), f'{self.label}: empty {name}')
                self.links.append(value)
            if name == 'style':
                require(not re.search(r'url\s*\(|expression\s*\(', value or '', re.I),
                        f'{self.label}: active/external inline style')
        if tag not in VOID_TAGS:
            self.stack.append(tag)

    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs)
        if tag not in VOID_TAGS:
            self.handle_endtag(tag)

    def handle_endtag(self, tag):
        if tag in VOID_TAGS:
            return
        require(self.stack and self.stack[-1] == tag,
                f'{self.label}: mismatched </{tag}>, open stack {self.stack[-5:]}')
        self.stack.pop()

    def handle_data(self, data):
        self.text.append(data)

    def finish(self, value):
        self.feed(value)
        self.close()
        require(not self.stack, f'{self.label}: unclosed HTML tags {self.stack}')
        text = ''.join(self.text)
        require(not RAW_TEX.search(text), f'{self.label}: raw LaTeX in displayed text')
        return len(re.findall(r'[\u3400-\u9fff]', text))


def number(value, label):
    require(isinstance(value, str) and re.fullmatch(r'\s*[+]?(?:\d+(?:\.\d*)?|\.\d+)(?:px)?\s*', value),
            f'{label}: absolute positive intrinsic dimension required, got {value!r}')
    result = float(value.strip().removesuffix('px'))
    require(math.isfinite(result) and result > 0, f'{label}: nonpositive dimension')
    return result


def image_size(path):
    """Read intrinsic size without Pillow, a browser, or native executables."""
    if path.suffix.lower() == '.svg':
        svg_text = path.read_text(encoding='utf-8')
        require(not PRIVATE.search(svg_text), f'{path.name}: private path inside SVG')
        require(not re.search(r'<!DOCTYPE|<!ENTITY|@import', svg_text, re.I),
                f'{path.name}: SVG external declaration/import')
        for css_url in re.findall(r'url\(\s*([^)]*?)\s*\)', svg_text, re.I):
            require(css_url.strip("\"' ").startswith('#'),
                    f'{path.name}: nonlocal SVG CSS resource {css_url}')
        root = ET.fromstring(svg_text)
        require(root.tag == '{'+SVG_NS+'}svg', f'{path.name}: not an SVG root')
        width = number(root.get('width'), path.name+' width')
        height = number(root.get('height'), path.name+' height')
        try:
            box = [float(x) for x in re.split(r'[\s,]+', root.get('viewBox', '').strip())]
        except ValueError as exc:
            raise ValueError(f'{path.name}: invalid viewBox') from exc
        require(len(box) == 4 and all(math.isfinite(x) for x in box)
                and box[2] > 0 and box[3] > 0, f'{path.name}: missing/invalid viewBox')
        require(math.isclose(width/height, box[2]/box[3], rel_tol=1e-6),
                f'{path.name}: intrinsic size and viewBox aspect ratios disagree')
        for elem in root.iter():
            require(local_name(elem.tag) not in ('script', 'foreignObject'),
                    f'{path.name}: active SVG element {elem.tag}')
            for key, value in elem.attrib.items():
                require(not local_name(key).lower().startswith('on'),
                        f'{path.name}: SVG inline event handler')
                require(not PRIVATE.search(value), f'{path.name}: private SVG path')
                if local_name(key) in ('href', 'src'):
                    require(value.startswith('#'), f'{path.name}: nonlocal SVG dependency {value}')
        return width, height
    data = path.read_bytes()
    if data.startswith(b'\x89PNG\r\n\x1a\n') and len(data) >= 24:
        return struct.unpack('>II', data[16:24])
    if data[:6] in (b'GIF87a', b'GIF89a') and len(data) >= 10:
        return struct.unpack('<HH', data[6:10])
    if data[:4] == b'RIFF' and data[8:12] == b'WEBP':
        offset = 12
        while offset + 8 <= len(data):
            kind, size = data[offset:offset+4], int.from_bytes(data[offset+4:offset+8], 'little')
            chunk = data[offset+8:offset+8+size]
            if kind == b'VP8X' and len(chunk) >= 10:
                return 1+int.from_bytes(chunk[4:7], 'little'), 1+int.from_bytes(chunk[7:10], 'little')
            if kind == b'VP8 ' and len(chunk) >= 10 and chunk[3:6] == b'\x9d\x01\x2a':
                return int.from_bytes(chunk[6:8], 'little') & 0x3fff, int.from_bytes(chunk[8:10], 'little') & 0x3fff
            if kind == b'VP8L' and len(chunk) >= 5 and chunk[0] == 0x2f:
                bits = int.from_bytes(chunk[1:5], 'little')
                return (bits & 0x3fff)+1, ((bits >> 14) & 0x3fff)+1
            offset += 8 + size + size % 2
    if data[:2] == b'\xff\xd8':
        offset = 2
        while offset+4 <= len(data):
            if data[offset] != 0xff:
                offset += 1
                continue
            marker = data[offset+1]
            offset += 2
            if marker in (0xd8, 0xd9, 0x01) or 0xd0 <= marker <= 0xd7:
                continue
            size = int.from_bytes(data[offset:offset+2], 'big')
            require(size >= 2, f'{path.name}: malformed JPEG segment')
            if marker in (0xc0, 0xc1, 0xc2, 0xc3, 0xc5, 0xc6, 0xc7, 0xc9, 0xca, 0xcb, 0xcd, 0xce, 0xcf):
                return int.from_bytes(data[offset+5:offset+7], 'big'), int.from_bytes(data[offset+3:offset+5], 'big')
            offset += size
    raise ValueError(f'{path.name}: unsupported or malformed image header')


class Validator:
    def __init__(self, site, allow_incomplete=False):
        self.site, self.allow_incomplete = site.resolve(), allow_incomplete
        self.data = self.site / 'dsp-redraw'
        self.errors, self.notes, self.results = [], [], []
        self.math_count = 0
        self.figure_paths, self.image_cache = set(), {}
        self.section_ids, self.anchor_cache = {}, {}

    def resource(self, url, label, image=False, local_only=False):
        require(isinstance(url, str) and url.strip() == url and url, f'{label}: empty/bad URL')
        require(not PRIVATE.search(unquote(url)), f'{label}: private/local-machine URL {url}')
        parsed = urlsplit(url)
        require(parsed.scheme.lower() not in ('javascript', 'data', 'file', 'blob'),
                f'{label}: unsafe URL scheme')
        if parsed.scheme or parsed.netloc:
            require(not local_only and parsed.scheme == 'https' and parsed.hostname
                    and not parsed.username and not parsed.password, f'{label}: nonlocal/unsafe resource {url}')
            require(not re.search(r'(?:^|\.)(?:example\.(?:com|org|net)|invalid|localhost)$', parsed.hostname),
                    f'{label}: placeholder URL {url}')
            return None  # Public citations: syntax checked, not network availability.
        require(not re.search(r'\{[^}]*\}|\b(?:TODO|TBD|PLACEHOLDER)\b', url, re.I),
                f'{label}: unresolved placeholder URL {url}')
        raw = unquote(parsed.path).removeprefix('/study-site/')
        require(not raw.startswith('/'), f'{label}: unrooted site URL {url}')
        if not raw:
            require(bool(parsed.fragment), f'{label}: empty target')
            return None
        target = (self.site / raw).resolve()
        require(target.is_relative_to(self.site) and target.is_file(), f'{label}: missing/public-path escape: {url}')
        if parsed.fragment and target.suffix == '.html':
            fragment = unquote(parsed.fragment)
            if target.name in ('dsp-ch2-redraw.html', 'dsp-course-redraw.html') and fragment.split('/')[0] in self.section_ids:
                parts = fragment.split('/')
                require(len(parts) <= 2 and (len(parts) == 1 or parts[1] in self.section_ids[parts[0]]),
                        f'{label}: invalid dynamic card anchor {fragment}')
            else:
                if target not in self.anchor_cache:
                    self.anchor_cache[target] = set(re.findall(r'\b(?:id|name)\s*=\s*[\"\']([^\"\']+)', target.read_text(encoding='utf-8')))
                require(fragment in self.anchor_cache[target], f'{label}: missing HTML anchor #{fragment}')
        if image:
            if target not in self.image_cache:
                self.image_cache[target] = image_size(target)
            width, height = self.image_cache[target]
            require(width > 0 and height > 0, f'{label}: image has empty intrinsic dimensions')
            return target, width, height
        return target

    def markup(self, value, label):
        parser = Fragment(label)
        chars = parser.finish(value)
        for url in parser.links:
            self.resource(url, label)
        return chars

    def scan(self, value, label):
        for path, text in walk(value, label):
            require(not PRIVATE.search(text), f'{path}: leaked private/local-machine path')
            self.math_count += math_blocks(text, path)
            if path.endswith('Html'):
                self.markup(text, path)
            if path.endswith(('.href', '.readerUrl')):
                self.resource(text, path, local_only=path.endswith('.readerUrl'))

    def figures(self, value, label):
        if isinstance(value, dict):
            require(not (value.get('figure') and value.get('figures')),
                    f'{label}: figure and figures both present; one would be silently hidden')
            if 'src' in value:
                require(isinstance(value.get('alt'), str) and value['alt'].strip(), f'{label}: figure needs alt text')
                target, width, height = self.resource(value['src'], label, image=True, local_only=True)
                require(target.suffix.lower() == '.svg', f'{label}: redraw figure must be vector SVG')
                require(width >= 620 and height >= 100, f'{label}: unreadably small redraw {width}x{height}')
                self.figure_paths.add(target)
            for key, child in value.items():
                self.figures(child, f'{label}.{key}')
        elif isinstance(value, list):
            for i, child in enumerate(value):
                self.figures(child, f'{label}[{i}]')

    def section(self, record, d):
        label = record['redrawData']
        source = d['source']
        count = record['sourcePageCount']
        require(source['pageCount'] == count and source['title'] == record['sourceFilename'],
                f'{label}: source title/pageCount differs from manifest')
        if source.get('sha256'):
            require(source['sha256'] == record['sha256'], f'{label}: source SHA256 metadata mismatch')
        pages = page_set(source.get('includedPages', list(range(1, count+1))), count, label+'.source.includedPages')
        require(pages == set(record['includedPages']), f'{label}: includedPages differs from manifest (split decks must list physical pages)')
        require(d.get('title') and d.get('brief'), f'{label}: missing title/brief')
        require(str(d.get('number')) == str(record['section']), f'{label}: navigation section number mismatch')
        self.scan(d, label)
        self.figures(d, label)
        if source.get('imagePattern'):
            pattern = source['imagePattern']
            require(isinstance(pattern, str) and pattern.count('{page}') == 1,
                    f'{label}: imagePattern needs exactly one {{page}} token')
            for page in sorted(pages):
                self.resource(pattern.replace('{page}', str(page)),
                              f'{label}.source.imagePattern page {page}', image=True, local_only=True)
        cards = d['cards']
        require(isinstance(cards, list) and 1 <= len(cards) <= 18, f'{label}: invalid/excessive card count')
        ids = [c['id'] for c in cards]
        require(len(ids) == len(set(ids)) and 'representative-example' not in ids, f'{label}: duplicate/reserved card ID')
        forward = set()
        essential = 0
        words = 0
        for c in cards:
            cid = c['id']
            require(re.fullmatch(r'[a-z0-9]+(?:-[a-z0-9]+)*', cid), f'{label}: bad card ID {cid}')
            require(c.get('title') and c.get('bodyHtml'), f'{label}/{cid}: missing teaching content')
            require(c.get('level') in ('essential', 'deep'), f'{label}/{cid}: invalid level')
            cp = page_set(c['sourcePages'], count, f'{label}/{cid}.sourcePages')
            require(cp <= pages, f'{label}/{cid}: source page outside section includedPages')
            forward.update((cid, p) for p in cp)
            if c['level'] == 'essential':
                essential += 1
                words += self.markup(c['bodyHtml'], f'{label}/{cid}.bodyHtml')
                if c.get('check'):
                    words += len(re.findall(r'[\u3400-\u9fff]', c['check'].get('question', '')))
                    words += self.markup(c['check'].get('answerHtml', ''), f'{label}/{cid}.check')
        require(1 <= essential <= 8, f'{label}: {essential} essential cards exceeds first-pass budget (8)')
        example = d.get('example')
        require(isinstance(example, dict) and example.get('title'), f'{label}: missing one representative example')
        ep = page_set(example.get('sourcePages', []), count, label+'.example.sourcePages', allow_empty=True)
        require(ep <= pages, f'{label}: example outside includedPages')
        if not ep:
            require('新编' in (example['title'] + example.get('problemHtml', '')),
                    f'{label}: unsourced example must clearly say 新编')
        for field in ('problemHtml', 'stepsHtml', 'answerHtml', 'checkHtml'):
            require(example.get(field), f'{label}: incomplete example.{field}')
            words += self.markup(example[field], label+'.example.'+field)
        mapped = d['pageMap']
        require(len(mapped) == len(pages) and {x['page'] for x in mapped} == pages,
                f'{label}: pageMap must cover included physical pages exactly once')
        reverse, example_reverse = set(), set()
        for row in mapped:
            page = row['page']
            require(type(page) is int, f'{label}: noninteger map page')
            refs = row.get('cardIds', [])
            require(refs or row.get('note'), f'{label}: unexplained empty map page {page}')
            require(len(refs) == len(set(refs)), f'{label}: repeated card in pageMap {page}')
            for cid in refs:
                require(cid in ids or cid == 'representative-example', f'{label}: unknown card {cid}')
                if cid == 'representative-example':
                    example_reverse.add(page)
                else:
                    reverse.add((cid, page))
        require(forward == reverse, f'{label}: card/page bidirectional mismatch; missing map={sorted(forward-reverse)}, extra map={sorted(reverse-forward)}')
        covered = {p for _, p in forward}
        require((covered | ep) == pages, f'{label}: physical pages not closed by cards or complete example: {sorted(pages-covered-ep)}')
        require(example_reverse <= ep, f'{label}: example/pageMap provenance mismatch')
        if ep - example_reverse:
            self.notes.append(f'{label}: virtual example links omitted for pages {sorted(ep-example_reverse)}; renderer derives them from example.sourcePages (valid).')
        minutes = d['firstPassMinutes']
        require(type(minutes) is int and 1 <= minutes <= 35, f'{label}: first-pass estimate outside 1..35 minutes')
        require(isinstance(d.get('firstPass'), list) and 2 <= len(d['firstPass']) <= 6,
                f'{label}: firstPass needs 2..6 focused goals')
        require(words <= 2600, f'{label}: first-pass prose exceeds 2600 Chinese characters ({words})')
        self.results.append(dict(file=label, id=d['id'], sourcePages=len(pages), cards=len(cards),
                                 essentialCards=essential, firstPassChineseCharacters=words,
                                 estimatedFirstPassMinutes=minutes))

    def run(self):
        manifest = json.loads((self.data/'course-sources.json').read_text(encoding='utf-8'))
        self.scan(manifest, 'course-sources.json')
        records = manifest['sections']
        names = [r['redrawData'] for r in records]
        require(len(names) == len(set(names)), 'Manifest repeats a data file')
        require(set(names) <= EXPECTED_FILES, 'Unexpected course section data filename')
        if not self.allow_incomplete:
            require(set(names) == EXPECTED_FILES, f'Manifest must contain all {EXPECTED_SECTIONS} sections')
        loaded, decks, physical, occurrences = [], {}, set(), collections.Counter()
        for r in records:
            filename = r['redrawData']
            sha, count, title = r['sha256'], r['sourcePageCount'], r['sourceFilename']
            require(re.fullmatch(r'[a-f0-9]{64}', sha), f'{filename}: invalid source SHA256')
            require(type(count) is int and count > 0, f'{filename}: invalid source page count')
            pages = page_set(r['includedPages'], count, filename+'.manifest.includedPages')
            require(sha not in decks or decks[sha] == (title, count), f'{filename}: inconsistent shared source identity')
            decks[sha] = (title, count)
            target = self.data/filename
            if not target.is_file() and self.allow_incomplete:
                self.notes.append(f'STAGED: missing {filename}; excluded from integrated totals')
                continue
            require(target.is_file(), f'Missing section: {filename}')
            d = json.loads(target.read_text(encoding='utf-8'))
            expected_id = ('dsp-fourier-supplement' if filename == 'supplement-fourier.json'
                           else 'dsp-'+filename.split('-')[1].removesuffix('.json'))
            require(d.get('id') == expected_id, f'{filename}: section ID must be {expected_id}')
            require(d.get('id') not in self.section_ids, f'{filename}: duplicate section ID')
            self.section_ids[d['id']] = {c['id'] for c in d['cards']} | {'representative-example'}
            loaded.append((r, d))
            physical.update((sha, page) for page in pages)
            occurrences.update((sha, page) for page in pages)
        for r, d in loaded:
            try:
                self.section(r, d)
            except (ValueError, KeyError, TypeError, ET.ParseError) as exc:
                self.errors.append(f'{r["redrawData"]}: {exc}')
        duplicates = [f'{decks[sha][0]} P{p}' for (sha, p), n in occurrences.items() if n > 1]
        require(not duplicates, f'Physical source pages assigned to multiple sections: {duplicates}')
        if not self.allow_incomplete:
            require(len(loaded) == EXPECTED_SECTIONS and len(decks) == EXPECTED_DECKS,
                    f'Expected {EXPECTED_SECTIONS} sections / {EXPECTED_DECKS} source decks')
            require(len(physical) == EXPECTED_PAGES, f'Expected {EXPECTED_PAGES} distinct physical pages, got {len(physical)}')
            for sha, (_, count) in decks.items():
                require({p for key, p in physical if key == sha} == set(range(1, count+1)),
                        f'Source deck not covered in full: {decks[sha][0]}')
            require(manifest.get('totalSourcePages') == EXPECTED_PAGES
                    and manifest.get('currentlyIntegratedPages') == EXPECTED_PAGES
                    and manifest.get('sourceDeckCount') == EXPECTED_DECKS,
                    'Manifest total/deck counters disagree with physical-page calculation')
            actual = {x.resolve() for x in (self.data/'assets').glob('*.svg')}
            require(len(actual) == EXPECTED_SVGS, f'Expected {EXPECTED_SVGS} SVG assets, got {len(actual)}')
            if not self.errors:
                require(self.figure_paths == actual, 'Referenced SVGs differ from asset directory (orphan or missing asset)')
        chapter_two_minutes = sum(x['estimatedFirstPassMinutes'] for x in self.results if x['id'].startswith('dsp-2'))
        require(chapter_two_minutes <= 150, f'Chapter 2 first-pass estimate exceeds 150 minutes ({chapter_two_minutes})')
        for filename in ('dsp-redraw.js', 'dsp-course-redraw.js'):
            target = self.site/filename
            if target.is_file():
                require(not re.search(r'localStorage\s*\.\s*(?:setItem|removeItem|clear)\s*\(', target.read_text(encoding='utf-8')),
                        f'{filename}: redraw reader writes old progress storage')
        return dict(ok=not self.errors, staged=self.allow_incomplete, sections=len(loaded),
                    sourceDecks=len({sha for sha, _ in physical}), distinctPhysicalPages=len(physical),
                    referencedSvgAssets=len(self.figure_paths), checkedImages=len(self.image_cache),
                    mathmlBlocks=self.math_count, sectionResults=self.results,
                    notes=self.notes, errors=self.errors,
                    limitations=['Structural checks do not replace mathematical/semantic or visual review.',
                                 'Original PPT hashes are checked as public metadata; private originals are never read.',
                                 'External citation URLs are syntax checked offline, not fetched.'])


def self_test():
    passed = 0
    def rejects(fn):
        nonlocal passed
        try:
            fn()
        except (ValueError, ET.ParseError):
            passed += 1
        else:
            raise AssertionError('Negative fixture unexpectedly passed')
    for tag, arity in ARITY.items():
        good = f'<math xmlns="{MATH_NS}"><{tag}>'+('<mi>x</mi>'*arity)+f'</{tag}></math>'
        require(math_blocks(good, 'fixture') == 1, 'Valid arity fixture failed')
        passed += 1
        for n in (arity-1, arity+1):
            bad = f'<math xmlns="{MATH_NS}"><{tag}>'+('<mi>x</mi>'*n)+f'</{tag}></math>'
            rejects(lambda b=bad: math_blocks(b, 'negative fixture'))
    rejects(lambda: Fragment('fixture').finish('<p>0<N</p>'))
    rejects(lambda: Fragment('fixture').finish('<p><strong>x</p></strong>'))
    rejects(lambda: Fragment('fixture').finish('<p onclick="x()">x</p>'))
    require(Fragment('fixture').finish('<p>0&lt;N</p>') == 0, 'Escaped inequality rejected')
    passed += 1
    rejects(lambda: page_set([1, 1], 4, 'fixture'))
    rejects(lambda: page_set([0, 2], 4, 'fixture'))
    require(len({('same-deck', p) for pages in ([1, 2], [2, 3]) for p in pages}) == 3,
            'Physical-page dedup fixture failed')
    passed += 1
    with tempfile.TemporaryDirectory(prefix='dsp-validator-selftest-') as tmp:
        path = Path(tmp)/'figure.svg'
        path.write_text(f'<svg xmlns="{SVG_NS}" width="640" height="320" viewBox="0 0 640 320"/>')
        require(image_size(path) == (640, 320), 'SVG intrinsic fixture failed')
        passed += 1
        path.write_text(f'<svg xmlns="{SVG_NS}" width="100%" height="320" viewBox="0 0 640 320"/>')
        rejects(lambda: image_size(path))
        path.write_text(f'<svg xmlns="{SVG_NS}" width="640" height="320" viewBox="0 0 640 320"><script/></svg>')
        rejects(lambda: image_size(path))
        validator = Validator(Path(tmp))
        rejects(lambda: validator.resource('/workspace/private.png', 'fixture'))
        rejects(lambda: validator.resource('not-built.html', 'fixture', local_only=True))
        rejects(lambda: validator.resource('https://example.com/fake', 'fixture'))
        rejects(lambda: validator.resource('javascript:alert(1)', 'fixture'))
    print(f'PASS self-test: {passed} positive/negative standard-library fixtures')


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--site', type=Path, default=ROOT/'site', help='public site directory (default: repository site/)')
    parser.add_argument('--allow-incomplete', action='store_true', help='explicit staged integration; do not use for release CI')
    parser.add_argument('--json-out', type=Path, help='optional machine-readable result; no writes by default')
    parser.add_argument('--self-test', action='store_true', help='run validator regression fixtures without course files')
    args = parser.parse_args()
    if args.self_test:
        self_test()
        return 0
    validator = Validator(args.site, args.allow_incomplete)
    try:
        result = validator.run()
    except (ValueError, KeyError, TypeError, OSError, json.JSONDecodeError, ET.ParseError) as exc:
        result = dict(ok=False, errors=validator.errors+[str(exc)], notes=validator.notes)
    if args.json_out:
        args.json_out.write_text(json.dumps(result, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    for row in result.get('sectionResults', []):
        print(f'PASS {row["file"]}: {row["sourcePages"]} physical pages; {row["cards"]} cards '
              f'({row["essentialCards"]} essential); first pass {row["firstPassChineseCharacters"]} '
              f'Chinese characters + formulas, estimated {row["estimatedFirstPassMinutes"]} min')
    for note in result.get('notes', []):
        print('NOTE '+note)
    for error in result.get('errors', []):
        print('FAIL '+error, file=sys.stderr)
    if result['ok']:
        print(f'PASS course: {result["sections"]} sections / {result["sourceDecks"]} decks / '
              f'{result["distinctPhysicalPages"]} distinct physical pages / '
              f'{result["referencedSvgAssets"]} SVGs / {result["mathmlBlocks"]} MathML blocks; '
              'standard library + public files only')
    return 0 if result['ok'] else 1


if __name__ == '__main__':
    sys.exit(main())
