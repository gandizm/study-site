#!/usr/bin/env python3
"""Losslessly assemble the reviewed homework assets from small, hash-checked Git objects.

No network, packages, archive extraction, or runtime browser loader is involved.
Use --pack after deliberately editing/rebuilding the reviewed generated assets.
"""
from pathlib import Path
import argparse
import base64
import hashlib
import json
import re
import zlib

ROOT = Path(__file__).resolve().parents[1]
PARTS = ROOT / 'source-parts/em-week1011'
TARGETS = (
    'site/em-week1011-homework.html',
    'site/em-week1011-answers.html',
)

RAW_PART_SIZE = 49152  # Base64 object size is at most 65536 bytes.
MAX_OUTPUT_SIZE = 12000000


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def pack(root=ROOT, parts=PARTS):
    parts.mkdir(parents=True, exist_ok=True)
    entries = []
    for target in TARGETS:
        source = (root / target).read_bytes()
        if not 0 < len(source) <= MAX_OUTPUT_SIZE:
            raise ValueError('Unexpected output size: ' + target)
        compressed = zlib.compress(source, level=9)
        chunks = []
        for number, offset in enumerate(range(0, len(compressed), RAW_PART_SIZE), 1):
            content = base64.b64encode(compressed[offset:offset + RAW_PART_SIZE])
            name = f'{Path(target).name}.{number:03}.b64'
            (parts / name).write_bytes(content)
            chunks.append({'file': name, 'bytes': len(content), 'sha256': sha256(content)})
        entries.append({'target': target, 'bytes': len(source), 'sha256': sha256(source), 'chunks': chunks})
    manifest = {'version': 1, 'encoding': 'zlib+base64', 'files': entries}
    (parts / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
    return entries


def read_verified(parts=PARTS):
    manifest = json.loads((parts / 'manifest.json').read_text())
    if manifest.get('version') != 1 or manifest.get('encoding') != 'zlib+base64':
        raise ValueError('Unsupported manifest')
    entries = manifest['files']
    if [entry['target'] for entry in entries] != list(TARGETS):
        raise ValueError('Unexpected output targets; no unrelated paths may be written')
    verified = []
    for entry in entries:
        target, size = entry['target'], entry['bytes']
        if type(size) is not int or not 0 < size <= MAX_OUTPUT_SIZE:
            raise ValueError('Invalid output size: ' + target)
        compressed = bytearray()
        if not 0 < len(entry['chunks']) <= 100:
            raise ValueError('Invalid part count')
        for number, chunk in enumerate(entry['chunks'], 1):
            expected_name = f'{Path(target).name}.{number:03}.b64'
            if chunk['file'] != expected_name or not re.fullmatch(r'[a-zA-Z0-9_.-]+', chunk['file']):
                raise ValueError('Invalid part name')
            path = parts / chunk['file']
            if path.is_symlink():
                raise ValueError('Part must not be a symlink')
            data = path.read_bytes()
            if len(data) != chunk['bytes'] or len(data) > 65536 or sha256(data) != chunk['sha256']:
                raise ValueError('Part checksum/size mismatch: ' + chunk['file'])
            compressed.extend(base64.b64decode(data, validate=True))
        inflater = zlib.decompressobj()
        source = inflater.decompress(compressed, size + 1)
        if len(source) != size or not inflater.eof or inflater.unused_data or inflater.unconsumed_tail:
            raise ValueError('Output size or compression stream mismatch: ' + target)
        if sha256(source) != entry['sha256']:
            raise ValueError('Output checksum mismatch: ' + target)
        verified.append((target, source))
    return verified


def assemble(root=ROOT, parts=PARTS):
    # Verify every part and output before writing any generated file.
    verified = read_verified(parts)
    for target, source in verified:
        output = root / target
        output.parent.mkdir(parents=True, exist_ok=True)
        if output.is_symlink() or root.resolve() not in output.resolve().parents:
            raise ValueError('Output must stay inside the build directory')
        temp = output.with_name(output.name + '.assembling')
        temp.write_bytes(source)
        temp.replace(output)
    return verified


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--pack', action='store_true', help='Split reviewed generated assets into small source objects')
    parser.add_argument('--check', action='store_true', help='Verify all parts without writing outputs')
    args = parser.parse_args()
    if args.pack:
        result = pack()
        print(f'Packed {len(result)} assets; each Git payload is at most 65536 bytes.')
    elif args.check:
        result = read_verified()
        print(f'Verified {len(result)} complete assets and all part checksums.')
    else:
        result = assemble()
        print(f'Assembled {len(result)} byte-identical assets from small checked source parts.')
