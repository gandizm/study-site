"""Small-object limits, complete reconstruction, and fail-closed integrity tests."""
from pathlib import Path
import importlib.util
import json
import shutil
import tempfile

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('em_parts', ROOT / 'scripts/assemble-em-energy-wedge.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
parts = ROOT / 'source-parts/em-energy-wedge'
manifest = json.loads((parts / 'manifest.json').read_text())
assert max(p.stat().st_size for p in parts.iterdir() if p.is_file()) < 100000
verified = module.read_verified(parts)
assert len(verified) == 4
assert len(dict(verified)['site/em-energy-wedge-homework.html']) > 1900000
assert dict(verified)['site/em-energy-wedge-homework.html'].count(b'data-tex=') == 354
with tempfile.TemporaryDirectory() as temp:
    root = Path(temp)
    module.assemble(root, parts)
    for target, data in verified:
        assert (root / target).read_bytes() == data
    damaged = root / 'damaged-parts'
    shutil.copytree(parts, damaged)
    chunk = damaged / manifest['files'][0]['chunks'][0]['file']
    content = chunk.read_bytes()
    chunk.write_bytes(bytes([content[0] ^ 1]) + content[1:])
    try:
        module.assemble(root, damaged)
        raise AssertionError('Corrupted source was accepted')
    except ValueError as error:
        assert 'checksum/size mismatch' in str(error)
    for target, data in verified:
        assert (root / target).read_bytes() == data
    altered = dict(manifest)
    altered['files'] = [dict(entry) for entry in manifest['files']]
    altered['files'][0]['target'] = 'site/data-structures-homework4.html'
    (damaged / 'manifest.json').write_text(json.dumps(altered))
    try:
        module.read_verified(damaged)
        raise AssertionError('Unexpected target was accepted')
    except ValueError as error:
        assert 'Unexpected output targets' in str(error)
print('PASS: all Git payloads below 100KB; 4 byte-identical assets; 354 formulas; corruption and unrelated-target writes rejected.')
