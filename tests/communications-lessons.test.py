#!/usr/bin/env python3
"""Static publication contracts and independent numerical checks for Comm 5–7."""
from pathlib import Path
from html.parser import HTMLParser
from urllib.parse import urlsplit, unquote
import unittest, json, math, re
import xml.etree.ElementTree as ET

ROOT=Path(__file__).resolve().parents[1]
SITE=ROOT/'site'

class Audit(HTMLParser):
    def __init__(self,text):
        super().__init__();self.ids=[];self.hrefs=[];self.images=[];self.math=0;self.units=[];self.deep=0;self.copy=0;self.external_scripts=[];self.details=[];self.feed(text)
    def handle_starttag(self,tag,attrs):
        a=dict(attrs)
        if 'id' in a:self.ids.append(a['id'])
        if tag=='a' and a.get('href'):self.hrefs.append(a['href'])
        if tag=='img' and a.get('src'):self.images.append(a)
        if tag=='math':self.math+=1
        if tag=='article' and a.get('class')=='comm-unit':self.units.append(a)
        if tag=='details' and a.get('class')=='deep-block':
            self.deep+=1;self.details.append(a)
        if 'data-copy-answer' in a:self.copy+=1
        if tag=='script' and a.get('src','').startswith(('http:','https:','//')):self.external_scripts.append(a['src'])

class Publication(unittest.TestCase):
    def setUp(self):
        self.course=(SITE/'communications-course-redraw.html').read_text()
        self.homework=(SITE/'communications-ch5-homework.html').read_text()
        self.meta=json.loads((SITE/'communications-redraw/source-map.json').read_text())
    def test_chapters_and_questions(self):
        c=Audit(self.course);h=Audit(self.homework)
        counts={ch:sum(u['data-chapter']==ch for u in c.units) for ch in ['intro','ch5','ch6','ch7']}
        self.assertEqual(counts,{'intro':4,'ch5':12,'ch6':10,'ch7':12})
        self.assertEqual([u['id'] for u in h.units],['q1','q3','q9','q13','q14','q15','q20','q25'])
        self.assertEqual(h.copy,8)
        self.assertEqual([x['physicalPages'] for x in self.meta['chapters']],[141,116,125])
        self.assertTrue(all(x['published'] for x in self.meta['chapters']))
    def test_formula_and_default_pass(self):
        for raw in [self.course,self.homework]:
            a=Audit(raw)
            self.assertGreater(a.math,100)
            self.assertFalse(a.external_scripts)
            self.assertTrue(all('open' not in d for d in a.details),'Second pass must begin collapsed')
            self.assertGreater(a.deep,0)
            # Math must actually be rendered, not left as a TeX fallback span.
            self.assertNotRegex(raw,r'<span class="math (?:inline|display)">\s*\\')
    def test_links_ids_assets_and_privacy(self):
        for raw in [self.course,self.homework]:
            a=Audit(raw)
            self.assertEqual(len(a.ids),len(set(a.ids)))
            for href in a.hrefs:
                if href.startswith('#') and len(href)>1:self.assertIn(unquote(href[1:]),a.ids)
                if not urlsplit(href).scheme and not href.startswith('#'):
                    path=urlsplit(href).path
                    target=SITE/path.removeprefix('/study-site/')
                    self.assertTrue(target.exists(),str(target))
            for img in a.images:
                self.assertTrue(img.get('alt'))
                target=SITE/urlsplit(img['src']).path
                self.assertTrue(target.exists(),str(target))
                ET.parse(target)
            for forbidden in ['file:///','/workspace/','libfile_','api_key','access_token','cloud_threads','collaboration.']:
                self.assertNotIn(forbidden,raw)
        self.assertFalse(self.meta['homework']['scansPublished'])
    def test_reader_does_not_touch_progress(self):
        js=(SITE/'communications-redraw.js').read_text()
        self.assertNotRegex(js,r'\b(?:localStorage|sessionStorage|indexedDB|fetch|XMLHttpRequest)\b')
        self.assertNotIn('course-reading-',js)
    def test_viewbox_svg_readable_size(self):
        js=(SITE/'communications-redraw.js').read_text()
        self.assertEqual(js.count('figureWidth = Math.max(1000, figureImage.naturalWidth || 0);'),2)
        self.assertIn('communications-redraw.js?v=20261110b',self.course)
        self.assertIn('communications-redraw.js?v=20261111-homework',self.homework)
    def test_novice_foundations_are_visible(self):
        def unit(raw, uid):
            match=re.search(r'<article id="'+re.escape(uid)+r'".*?</article>',raw,re.S)
            self.assertIsNotNone(match)
            return match.group(0)
        for i in range(12):
            block=unit(self.course,f'ch5-{i:02d}')
            self.assertIn('class="answer-check"',block)
            self.assertNotRegex(block,r'<details[^>]*class="answer-check"[^>]*\bopen(?:=|>)')
            first=re.search(r'<section class="lesson-block">.*?</section>',block,re.S).group(0)
            self.assertIn('零基础' if i<11 else '毕业小测',first)
        self.assertIn('第一遍可查',unit(self.course,'ch5-00'))
        self.assertGreaterEqual(self.homework.count('class="answer-check"'),15)
        for q in [1,3,9,15,20]:
            self.assertIn('class="answer-check"',unit(self.homework,'q'+str(q)))
        for figure in ['novice-signal-samples.svg','novice-spectrum-steps.svg','novice-sampling-types.svg']:
            self.assertIn(figure,self.course)

    def test_ch67_foundations_preserve_existing_units(self):
        ids = ['ch6-00','ch6-02','ch6-03','ch6-06','ch6-07',
               'ch7-00','ch7-01','ch7-03','ch7-04','ch7-10']
        for uid in ids:
            block = re.search(r'<article id="'+uid+r'".*?</article>', self.course, re.S).group(0)
            first = re.search(r'<section class="lesson-block">.*?</section>', block, re.S).group(0)
            self.assertIn('零基础', first)
        for name in ['pulse-convolution','noise-decision','eye-diagram','carrier-coherent','qpsk-iq']:
            self.assertIn('novice-'+name+'.svg', self.course)

    def test_reviewed_homework_answer_first(self):
        for q in [13,14,25]:
            block = re.search(r'<article id="q'+str(q)+r'".*?</article>', self.homework, re.S).group(0)
            self.assertIn('data-answer-first="true"',block)
            self.assertEqual(block.count('class="copy-answer"'),1)
            self.assertEqual(block.count('data-copy-answer'),1)
            self.assertLess(block.index('>原题</h3>'),block.index('>可抄解答</h3>'))
            self.assertLess(block.index('class="copy-answer"'),block.index('<details class="deep-block">'))
            self.assertIn('学习解释</summary>',block)
            self.assertNotIn('class="answer-check"',block)
            self.assertIn('来源与口径',block)
            self.assertNotRegex(block,r'<details[^>]*\bopen(?:=|>)')
        q25=re.search(r'<article id="q25".*?</article>',self.homework,re.S).group(0)
        self.assertIn('原题明确同时要求两种带宽',q25)
        self.assertIn('第一零点带宽为384 kHz，理论最小信道带宽为96 kHz',q25)
        self.assertNotIn('为什么有两个不同的带宽答案',q25)

    def test_leading_zero_codes(self):
        for code in ['11100011','01001110000','00110000','00001011110','01010011','00100111000']:
            self.assertIn(code,self.homework)

class NumericalChecks(unittest.TestCase):
    def test_sampling_overlap(self):
        def tri(f):return max(0,1-abs(f)/200)
        def spectrum(f,fs):return fs*sum(tri(f-k*fs) for k in range(-6,7))
        for f in [100,125,150,175,200]:self.assertAlmostEqual(spectrum(f,300),150)
        self.assertEqual(spectrum(0,300),300)
        self.assertEqual(spectrum(0,400),400)
        self.assertEqual(spectrum(200,400),0)
    def test_filter_then_sample(self):
        for u in [0,.25,.5,.75,1]:
            ts=1/3;h1=1-abs(u)/2;h2=ts/h1
            self.assertAlmostEqual(h1*h2/ts,1)
    def test_uniform_quantizer(self):
        self.assertEqual(math.ceil(math.log2(40)),6)
        step=20/40;self.assertEqual(step,.5)
        self.assertEqual(step/2,.25);self.assertEqual(20-step/2,19.75)
    def test_alaw(self):
        starts=[0,16,32,64,128,256,512,1024];steps=[1,1,2,4,8,16,32,64]
        def encode(x,folded=False):
            mag=abs(x);seg=max(i for i,l in enumerate(starts) if mag>=l);j=int((mag-starts[seg])//steps[seg])
            d=(7-j if j<8 else j) if folded else j
            code=('1' if x>=0 else '0')+f'{seg:03b}'+f'{d:04b}'
            q=(starts[seg]+(j+.5)*steps[seg])*(1 if x>=0 else -1)
            return code,q,f'{int(abs(q)):011b}'
        self.assertEqual(encode(635),('11100011',624,'01001110000'))
        self.assertEqual(encode(-95,True),('00110000',-94,'00001011110'))
        self.assertEqual(encode(-315),('01010011',-312,'00100111000'))
    def test_delta_and_tdm(self):
        f0=1000;M=1;fs=4000
        self.assertLessEqual(2*math.pi*f0*M/fs,1.8);self.assertLess(1.8,2*M)
        rs=24*8000;tau=.5/rs
        self.assertAlmostEqual(1/tau,384000);self.assertEqual(rs/2,96000)
    def test_raised_cosine_samples(self):
        def sinc(t):return 1 if not t else math.sin(math.pi*t)/(math.pi*t)
        def rc(t,a):
            if a and abs(abs(2*a*t)-1)<1e-9:return math.pi/4*sinc(1/(2*a))
            return sinc(t)*math.cos(math.pi*a*t)/(1-(2*a*t)**2)
        for a in [0,.5,1]:
            self.assertAlmostEqual(rc(0,a),1)
            for k in [-3,-2,-1,1,2,3]:self.assertAlmostEqual(rc(k,a),0,places=12)
    def test_qpsk_labels(self):
        labels={45:(0,0),135:(1,0),225:(1,1),315:(0,1)}
        for degrees,(u,v) in labels.items():
            I,Q=1-2*u,1-2*v
            self.assertEqual(round(math.degrees(math.atan2(Q,I)))%360,degrees)
            self.assertEqual(I*I+Q*Q,2)

if __name__=='__main__':unittest.main(verbosity=2)
