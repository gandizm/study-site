"""Validate the static, same-page SVGs, not just accessible labels or a sample page."""
from html import unescape
from pathlib import Path
import re
import xml.etree.ElementTree as ET

site = Path(__file__).resolve().parents[1] / 'site'
chapters = (0,1,2,3,5,6,7)
expected = (7,220,1122,31,168,174,144)
previews = (7,19,81,8,1,0,22)
formula = re.compile(r'<svg class="formula [^"]*em-companion-formula"[^>]*aria-label="([^"]*)"[^>]*data-tex="([^"]*)"[^>]*><use href="#([^"]+)"></use></svg>')
all_uses=0
width_witnesses=set()
for prefix,counts in (('ppt',expected),('em-math-preview-',previews)):
    for chapter,count in zip(chapters,counts):
        html=(site/f'{prefix}{chapter}.html').read_text()
        found=list(formula.finditer(html))
        assert len(found)>=count and (bool(found) or count==0),(prefix,chapter,len(found),count)
        all_uses+=len(found)
        # All legacy SVGs with fully scalar labels are left as authored.
        old=re.findall(r'<svg class="formula(?: | inline)"[^>]*aria-label="([^"]*)"',html)
        assert not any(re.search(r'\\(?:mathbf|boldsymbol|hat)(?![a-zA-Z])',unescape(s)) for s in old)
        if not found:continue
        sheet=re.search(r'<svg class="em-companion-defs"[\s\S]*?</defs></svg>',html);assert sheet
        sheet=ET.fromstring(sheet[0]);glyphs={e.get('id') for e in sheet.iter() if e.tag.endswith('path')}
        symbols={e.get('id'):e for e in sheet.iter() if e.tag.endswith('symbol')}
        refs=set()
        for occurrence in found:
            label,tex,ref=occurrence.groups()
            tex=unescape(tex);label=unescape(label)
            assert ref in symbols and tex.replace(r'\emvec{',r'\bar{').replace(r'\emunit{',r'\hat{').replace(r'\emdiff{',r'\overline{\mathrm d ')==label
            node=symbols[ref]
            # A symbol already maps its negative math baseline into a viewport.
            # Reapplying its negative y to the outer SVG puts its ink below the
            # visible instance (sometimes all glyphs disappear in browsers).
            outer=re.search(r'viewBox="([^"]+)"',occurrence[0])[1].split()
            assert outer[:2]==['0','0'] and outer[2:]==node.get('viewBox').split()[2:], (tex,outer)
            if ref in refs:continue
            refs.add(ref)
            leaves=list(node.iter())
            assert not any(x.get('data-mml-node')=='merror' for x in leaves)
            assert all(float(n)>0 for n in node.get('viewBox').split()[2:])
            for x in leaves:
                if x.tag.endswith('use'):
                    assert x.get('{http://www.w3.org/1999/xlink}href','')[1:] in glyphs
            assert r'\emvec{0}' not in tex and r'\emdiff{r}' not in tex
            # A full-width overline and a font's narrow fixed macron must both
            # fail: this is the reported defect, not just a count of accents.
            witness=re.fullmatch(r'\\emvec\{([AEr])\}',tex)
            if witness:
                rule=next(e for e in leaves if e.tag.endswith('svg') and e.get('width'))
                ratio=float(rule.get('width'))/float(node.get('viewBox').split()[2])
                assert .79<=ratio<=.94,(tex,ratio)
                width_witnesses.add(witness[1])
            # Each semantic accent has an actual SVG accent over its base.
            movers=[x for x in leaves if x.get('data-mml-node')=='mover']
            bars=hats=0
            for x in movers:
                if len(x)<2:continue
                accent=list(x)[-1]
                codes={el.get('data-c') for el in accent.iter()}
                if any(el.tag.endswith('rect') for el in accent.iter()) or bool({'AF','2013','2015','203E','2212'}&codes): bars+=1
                if bool({'2C6','5E','302'}&codes): hats+=1
            assert bars>=tex.count(r'\emvec{')+tex.count(r'\emdiff{'),(tex,bars)
            assert hats>=tex.count(r'\emunit{'),(tex,hats)
        assert refs==set(symbols)
        if prefix=='ppt':
            assert len(re.findall(r'<article\b[^>]*\bdata-page=',html))=={0:20,1:42,2:57,3:24,5:78,6:74,7:35}[chapter]
            if chapter==2:
                assert r'\emvec{S}=\emvec{E}\times\emvec{H}' in html
                for old_note in ('这里用粗体下标','P49的粗体','是外向面积元；粗体','这里无粗体的','原页用不加粗的'): assert old_note not in html
            if chapter==5:
                assert r'\dot{\emvec{E}}' in html and r'\bar w' in html
assert width_witnesses=={'A','E','r'},width_witnesses
print(f'PASS: {all_uses} static textbook-notation SVG occurrences, native accents, 330 original slide positions and complete in-page glyph references.')
