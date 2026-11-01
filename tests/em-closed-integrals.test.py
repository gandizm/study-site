"""Regression: closed surface integrals must be real glyphs, not silent TeX fallbacks."""
from pathlib import Path
import html
import re
import unittest

PAGE = Path(__file__).resolve().parents[1] / 'site/em-ch2-homework.html'

class ClosedSurfaceIntegrals(unittest.TestCase):
    def test_static_closed_integral_glyphs(self):
        source = PAGE.read_text()
        equations = re.findall(r'(<span class="hw-math[^>]*>)([\s\S]*?)(</span>)', source)
        affected = [(opening, body) for opening, body, _ in equations if r'\oiint' in opening]
        self.assertEqual(len(affected), 6, 'Cover all occurrences, including collapsed explanations')
        self.assertEqual(sum(html.unescape(re.search(r'data-tex="([^"]*)"', o)[1]).count(r'\oiint') for o, _ in affected), 7)
        for opening, body in affected:
            tex = html.unescape(re.search(r'data-tex="([^"]*)"', opening)[1])
            self.assertEqual(html.unescape(re.search(r'aria-label="([^"]*)"', opening)[1]), tex)
            self.assertEqual(len(re.findall(r'<path\b[^>]*data-c="222F"', body)), tex.count(r'\oiint'), tex)
            self.assertNotRegex(body, r'data-mml-node="merror"|data-c="5C"|<text\b|fill="red"', tex)
            self.assertNotRegex(body, r'(?:xlink:)?href="https?://', 'All glyphs must work offline')
            self.assertIn('aria-hidden="true"', body)

if __name__ == '__main__':
    unittest.main()
