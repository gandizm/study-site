#!/usr/bin/env python3
"""Regression checks for actual course examples and their corrected source errors.

Run from any directory: python tests/dsp-course-math.test.py
Python standard library only; no private source files, third-party numerics or web.

Provenance: public site/dsp-redraw JSON sourcePages and SVG metadata, specifically
1.3 P25-29; 1.4 P33-39; 3.2 P27/P39/P63-64; 3.3 P45-46;
3.4 P49-53 (textbook code corrections are explicitly distinguished in the cards).
Numerical evaluation points and impulse probes are test inputs, not invented
course examples. The tests do not claim browser or complete-course proof coverage.
"""
from pathlib import Path
from fractions import Fraction as Q
from html.parser import HTMLParser
import cmath
import json
import math
import re
import unittest
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
CONTENT = ROOT / 'site' / 'dsp-redraw'
PI = math.pi


class PlainText(HTMLParser):
    def __init__(self):
        super().__init__()
        self.parts = []

    def handle_data(self, data):
        self.parts.append(data)


def plain(html):
    parser = PlainText()
    parser.feed(html)
    return ''.join(parser.parts)


class TableRows(HTMLParser):
    """Read the published numeric answer table, rather than duplicate its answer."""
    def __init__(self):
        super().__init__()
        self.rows, self.row, self.cell = [], None, None

    def handle_starttag(self, tag, attrs):
        if tag == 'tr':
            self.row = []
        elif tag in ('th', 'td'):
            self.cell = []

    def handle_data(self, data):
        if self.cell is not None:
            self.cell.append(data)

    def handle_endtag(self, tag):
        if tag in ('th', 'td') and self.cell is not None:
            self.row.append(''.join(self.cell).strip())
            self.cell = None
        elif tag == 'tr' and self.row is not None:
            self.rows.append(self.row)
            self.row = None


def rows(html):
    parser = TableRows()
    parser.feed(html)
    return parser.rows


def rational(value):
    return Q(str(value).replace('−', '-'))


def sequence_from_problem(text, name):
    match = re.search(name + r'\[([−\-]?\d+)…([−\-]?\d+)\]=\{([^}]+)\}', text)
    if match is None:
        raise AssertionError('Published original sequence is missing: ' + name)
    start, stop = (int(v.replace('−', '-')) for v in match.group(1, 2))
    values = [rational(v) for v in match.group(3).split(',')]
    if len(values) != stop - start + 1:
        raise AssertionError('Original sequence support and samples disagree')
    return start, values


def load_section(name):
    return json.loads((CONTENT / (name + '.json')).read_text(encoding='utf-8'))


def original_card(section, card_id, source_pages):
    card = next(c for c in load_section(section)['cards'] if c['id'] == card_id)
    if not set(source_pages).issubset(card['sourcePages']):
        raise AssertionError('Lost original-page provenance: ' + card_id)
    return card


def svg_metadata(name):
    root = ET.parse(CONTENT / 'assets' / (name + '.svg')).getroot()
    node = root.find('{http://www.w3.org/2000/svg}metadata')
    if node is None or not node.text:
        raise AssertionError('Missing published numerical figure data: ' + name)
    return json.loads(node.text)


def convolution(x, h):
    return [sum(x[k] * h[n-k] for k in range(len(x)) if 0 <= n-k < len(h))
            for n in range(len(x) + len(h) - 1)]


def poly_add(a, b):
    return [(a[n] if n < len(a) else 0) + (b[n] if n < len(b) else 0)
            for n in range(max(len(a), len(b)))]


def poly_at(coefficients, x):
    """Ascending powers; Horner evaluation also works with exact Fractions."""
    result = 0
    for coefficient in reversed(coefficients):
        result = result * x + coefficient
    return result


def rational_sum(numerators, denominators):
    num, den = [Q(0)], [Q(1)]
    for b, a in zip(numerators, denominators):
        num = poly_add(convolution(num, a), convolution(b, den))
        den = convolution(den, a)
    return num, den


def dft(x):
    size = len(x)
    return [sum(v * cmath.exp(-2j * PI * k * n / size) for n, v in enumerate(x))
            for k in range(size)]


def idft(spectrum):
    size = len(spectrum)
    return [sum(v * cmath.exp(2j * PI * k * n / size)
                for k, v in enumerate(spectrum)) / size for n in range(size)]


def filter_zero_state(b, a, x):
    """Difference equation for A(q)y=B(q)x, normalized by a[0]."""
    y = []
    for n in range(len(x)):
        feedforward = sum(v * x[n-k] for k, v in enumerate(b) if n >= k)
        feedback = sum(a[k] * y[n-k] for k in range(1, len(a)) if n >= k)
        y.append((feedforward - feedback) / a[0])
    return y


class OriginalCourseRegressions(unittest.TestCase):
    def close(self, actual, expected, tolerance=1e-11):
        self.assertEqual(len(actual), len(expected))
        for index, (a, b) in enumerate(zip(actual, expected)):
            self.assertLessEqual(abs(a-b), tolerance, 'sample/index %s: %r != %r' % (index, a, b))

    def test_13_original_indexed_convolution(self):
        """P25-29: nonzero input origins and cancellation at n=5 are preserved."""
        example = load_section('ch1-13')['example']
        self.assertTrue(set(range(25, 30)).issubset(example['sourcePages']))
        problem = plain(example['problemHtml'])
        nx, x = sequence_from_problem(problem, 'x')
        nh, h = sequence_from_problem(problem, 'h')
        answer = rows(example['answerHtml'])
        actual = convolution(x, h)
        self.assertEqual(list(range(nx+nh, nx+nh+len(actual))),
                         [int(v.replace('−', '-')) for v in answer[0][1:]])
        self.assertEqual(actual, [rational(v) for v in answer[1][1:]])
        self.assertEqual(actual, list(map(Q, [8, 10, 13, 4.5, 3, 1, 0, .5])))
        self.assertEqual(sum(actual), sum(x) * sum(h))
        self.assertEqual(sum(actual), 40)
        # At absolute n=5, cancellation is not absence of overlap.
        terms = [x[k] * h[5-(nx+k)-nh] for k in range(len(x))
                 if 0 <= 5-(nx+k)-nh < len(h)]
        self.assertGreater(sum(v != 0 for v in terms), 1)
        self.assertEqual(sum(terms), 0)

    def test_14_original_sampling_and_nyquist_boundary(self):
        """P33-36: 50Hz/200Hz gives four samples; equality loses some phases."""
        example = load_section('ch1-14')['example']
        self.assertTrue({33, 34, 35}.issubset(example['sourcePages']))
        text = plain(example['problemHtml'])
        f0, phase_divisor = map(int, re.search(r'sin\(2π·(\d+)t\+π/(\d+)\)', text).groups())
        fs = int(re.search(r'f_s=(\d+)\s*Hz', text).group(1))
        self.assertEqual((f0, fs, phase_divisor), (50, 200, 8))
        samples = [math.sin(2*PI*f0*n/fs + PI/phase_divisor) for n in range(4)]
        published = [float(v.replace('−', '-')) for v in rows(example['answerHtml'])[1][1:]]
        self.close(samples, published, tolerance=5.1e-7)
        self.assertEqual(fs // f0, 4)
        self.assertAlmostEqual(4/fs, 1/f0)
        for n in range(12):
            self.assertAlmostEqual(math.sin(2*PI*f0*n/fs + PI/phase_divisor), samples[n % 4])
        card = original_card('ch1-14', 'natural-sampling-and-boundary', [36])
        self.assertIn('fₛ=2f₀', plain(card['bodyHtml']))
        equality_fs = 2 * f0
        zero_phase = [math.sin(2*PI*f0*n/equality_fs) for n in range(12)]
        quadrature = [math.sin(2*PI*f0*n/equality_fs + PI/2) for n in range(12)]
        self.close(zero_phase, [0]*12)
        self.close(quadrature, [(-1)**n for n in range(12)])
        self.assertLess(1/fs, 1/(2*f0))  # T=1/fs, not the false T<1/fs.

    def test_14_original_finite_z_roc_excludes_zero_and_infinity(self):
        """P38-39: retain the negative-time sample and both Laurent boundaries."""
        example = load_section('ch1-13')['example']
        start, x = sequence_from_problem(plain(example['problemHtml']), 'x')
        card = original_card('ch1-14', 'z-transform-start', [38, 39])
        compact = ''.join(plain(card['bodyHtml']).split())
        self.assertIn('z=0为三阶极点，z=∞为一阶极点', compact)
        powers = [-(start+n) for n, value in enumerate(x) if value]
        self.assertEqual(-min(powers), 3)  # pole at zero
        self.assertEqual(max(powers), 1)  # pole at infinity; x[-1] is not discarded
        # Coefficients from the displayed rational numerator, in ascending powers.
        numerator = [Q(1, 2), -1, Q(3, 2), 1, 2]
        for z in [.25+.5j, 1, 2-.7j]:
            series = sum(float(v) * z**(-(start+n)) for n, v in enumerate(x))
            self.assertAlmostEqual(abs(series-poly_at(numerator, z)/z**3), 0, places=11)
        self.assertEqual(sum(abs(v) for v in x), 6)  # finite absolute sum on |z|=1
        self.assertEqual(numerator[0], Q(1, 2))  # no cancellation of z^3 at zero
        self.assertEqual(numerator[-1], 2)       # no cancellation of leading degree

    def test_32_p27_signed_gains_and_direct_form_equivalence(self):
        """P27: the erroneous +2 feedforward tap must not return."""
        original_card('ch3-32', 'original-iir-numbers', [27])
        first = svg_metadata('32-original-direct-i')
        second = svg_metadata('32-direct-ii-example')
        b = [rational(v) for v in second['feedforward']]
        gains = [rational(v) for v in second['feedbackGains']]
        self.assertEqual(b, [8, -4, 11, -2])
        self.assertEqual(gains, [Q(5, 4), Q(-3, 4), Q(1, 8)])
        self.assertEqual(first['feedforward'], second['feedforward'])
        self.assertEqual([rational(v) for v in first['feedbackGains']], gains)
        self.assertEqual((first['delayCount'], second['delayCount']), (6, 3))
        a = [Q(1)] + [-v for v in gains]
        self.assertEqual(a, convolution([Q(1), Q(-1, 4)], [Q(1), Q(-1), Q(1, 2)]))
        impulse = [Q(1)] + [Q(0)]*31
        direct_i = filter_zero_state(b, a, impulse)
        state = [Q(0)]*3
        direct_ii = []
        for value in impulse:
            w = value + sum(g*s for g, s in zip(gains, state))
            direct_ii.append(b[0]*w + sum(g*s for g, s in zip(b[1:], state)))
            state = [w] + state[:-1]
        self.assertEqual(direct_i, direct_ii)  # exact rational equality, not rounding
        self.assertEqual(direct_i[:4], [8, 6, Q(25, 2), Q(81, 8)])
        for pole in [.25, .5+.5j, .5-.5j]:
            self.assertLess(abs(pole), 1)
            self.assertLess(abs(poly_at(list(reversed(a)), pole)), 1e-12)
        wrong_b = b[:-1] + [Q(2)]
        self.assertNotEqual(filter_zero_state(wrong_b, a, impulse)[3], direct_i[3])

    def test_32_p39_exact_partial_fraction_identity_and_old_error(self):
        """P39: correct -6/+6 branches; old +6/-6 gives -3 instead of 21."""
        original_card('ch3-32', 'original-cascade-parallel', [39])
        data = svg_metadata('32-original-parallel')
        num, den = rational_sum(data['numerators'], data['denominators'])
        expected_num, expected_den = [1, 2, 2, 1], [1, -2, 0, 1]
        self.assertEqual(convolution(num, expected_den), convolution(expected_num, den))
        self.assertEqual(expected_num, convolution([1, 1], [1, 1, 1]))
        self.assertEqual(expected_den, convolution([1, -1], [1, -1, -1]))
        q = Q(1, 2)
        correct = poly_at(num, q) / poly_at(den, q)
        self.assertEqual(correct, 21)
        old_num, old_den = rational_sum([[1], [6], [-6, 4]], [[1], [1, -1], [1, -1, -1]])
        self.assertEqual(poly_at(old_num, q)/poly_at(old_den, q), -3)
        self.assertEqual(poly_add(expected_num, [-v for v in old_num]), [0, 0, 12, 0])
        self.assertEqual(data['numerators'], [[1], [-6], [6, 4]])
        self.assertEqual(data['denominators'][2], [1, -1, -1])  # feedback +1,+1
        self.assertGreater((1+math.sqrt(5))/2, 1)  # original causal example is unstable

    def test_32_p64_seven_zeros_and_three_linear_phase_sections(self):
        """P63-64/book typo: c=3.2025, not 4.2025; the seven points are zeros."""
        original_card('ch3-32', 'original-seven-zeros', [63, 64])
        data = svg_metadata('32-original-zero-orbits')
        h = [rational(v) for v in data['coefficients']]
        fourth = [Q(1), Q(-205, 100), Q(32025, 10000), Q(-205, 100), Q(1)]
        self.assertEqual(fourth, convolution([Q(1), Q(-8, 10), Q(64, 100)],
                                            [Q(1), Q(-125, 100), Q(15625, 10000)]))
        self.assertEqual(h, convolution(convolution([1, 1], [1, -1, 1]), fourth))
        self.assertEqual(h, h[::-1])
        self.assertEqual(len(h), 8)
        self.assertEqual(poly_at(h, -1), 0)
        zeros = [complex(*v) for v in data['zeros']]
        expected = [-1] + [r*cmath.exp(1j*theta) for r in [1, .8, 1.25] for theta in [PI/3, -PI/3]]
        self.assertEqual(len(zeros), 7)
        for zero in expected:
            self.assertLess(min(abs(zero-v) for v in zeros), 1e-12)
            self.assertLess(abs(poly_at(list(reversed(h)), zero)), 1e-11)
        typo = fourth[:]
        typo[2] = Q(42025, 10000)
        self.assertNotEqual(h, convolution(convolution([1, 1], [1, -1, 1]), typo))

    def test_33_p45_p46_impulse_invariant_residues_and_both_intervals(self):
        """Actual Ha numerator .5012, denominator s²+.6449s+.7079; h[n]=ha(nT)."""
        card = original_card('ch3-33', 'corrected-impulse-example', [45, 46])
        text = plain(card['bodyHtml'])
        match = re.search(r'Hₐ\(s\)=([\d.]+)/\(s²\+([\d.]+)s\+([\d.]+)\)', text)
        self.assertIsNotNone(match, 'Original analog system must remain explicit')
        numerator, damping, constant = map(float, match.groups())
        self.assertEqual((numerator, damping, constant), (.5012, .6449, .7079))
        a = damping/2
        b = math.sqrt(constant-a*a)
        K = numerator/b
        # Correct original residues, checked against the actual analog rational function.
        for s in [1+2j, .4+.3j, 2]:
            decomposed = (1j*K/2)/(s+a+1j*b) + (-1j*K/2)/(s+a-1j*b)
            actual = numerator/(s*s+damping*s+constant)
            self.assertLess(abs(decomposed-actual), 1e-13)
            self.assertGreater(abs(-decomposed-actual), .01)  # source's swapped signs
        numeric_results = re.findall(
            r'T=([\d.]+)：H\(z\)≈([\d.]+)z⁻¹/\(1−([\d.]+)z⁻¹\+([\d.]+)z⁻²\)', text)
        self.assertEqual({float(v[0]) for v in numeric_results}, {1, .1})
        for period, published_b1, published_a1, published_a2 in numeric_results:
            T = float(period)
            r = math.exp(-a*T)
            coefficients = [K*r*math.sin(b*T), 2*r*math.cos(b*T), r*r]
            for calculated, shown in zip(coefficients, [published_b1, published_a1, published_a2]):
                decimals = len(shown.split('.')[1])
                self.assertLessEqual(abs(calculated-float(shown)), .5*10**(-decimals)+1e-12)
            b1, negative_a1, a2 = coefficients
            impulse = [1] + [0]*63
            recursive = filter_zero_state([0, b1], [1, -negative_a1, a2], impulse)
            sampled = [K*math.exp(-a*T*n)*math.sin(b*T*n) for n in range(len(impulse))]
            self.close(recursive, sampled)
            self.assertEqual(recursive[0], 0)
            self.assertGreater(recursive[1], 0)  # negative numerator would fail immediately
            self.assertLess(r, 1)
            if T == 1:
                self.assertGreater(abs(a2-.247), .25)  # incorrect original rounded coefficient
            else:
                self.assertGreater(abs(a2-math.exp(-2*a)), .4)  # omitted T is not harmless
                self.assertGreater(abs(recursive[1]-T*sampled[1]), .04)  # no silent T scaling

    def test_34_p49_p51_n12_type_iv_half_integer_center(self):
        """P50 correct complex samples, not P51/book's center=6 and missing IV phase."""
        card = original_card('ch3-34', 'original-highpass-bandpass', [49, 50, 51])
        highpass = plain(card['bodyHtml']).split('原例3.4.9')[0]
        N = int(re.search(r'N=2π/\(π/6\)=(\d+)', highpass).group(1))
        alpha = float(re.search(r'α=([\d.]+)', highpass).group(1))
        transition = float(re.search(r'A\(4\)=A\(8\)=([\d.]+)', highpass).group(1))
        self.assertEqual((N, alpha, transition), (12, 5.5, .39))
        self.assertEqual(alpha, (N-1)/2)
        A = [0]*N
        A[4] = A[8] = transition
        A[5] = A[6] = A[7] = 1
        H = [value*cmath.exp(-1j*(2*PI*k*alpha/N+PI/2)) for k, value in enumerate(A)]
        h = idft(H)
        printed = [float(v.replace('−', '-')) for v in re.search(r'约为\[([^]]+)\]', highpass).group(1).split(',')]
        self.close(h, printed, tolerance=5.1e-7)
        self.close([v.imag for v in h], [0]*N)
        self.close(h, [-v for v in reversed(h)])
        self.close(dft(h), H)
        self.assertLess(abs(sum(h)), 1e-12)
        self.assertLess(abs(sum(v*(-1)**n for n, v in enumerate(h))-1), 1e-12)
        self.assertIn('11πk/12+π/2', highpass)
        old = idft([value*cmath.exp(-2j*PI*k*(N/2)/N) for k, value in enumerate(A)])
        self.assertGreater(max(abs(old[n]+old[N-1-n]) for n in range(N)), .1)
        wrong_center_with_iv = idft([value*cmath.exp(-1j*(2*PI*k*(N/2)/N+PI/2))
                                    for k, value in enumerate(A)])
        self.assertGreater(max(abs(v.imag) for v in wrong_center_with_iv), .1)

    def test_34_p52_p53_n33_bandpass_missing_two_counterexample(self):
        """Original analytical 2/33 is correct; the book code's 1/33 halves the gain."""
        card = original_card('ch3-34', 'original-highpass-bandpass', [52, 53])
        bandpass = plain(card['bodyHtml']).split('原例3.4.9')[1]
        N = int(re.search(r'N=(\d+)', bandpass).group(1))
        alpha = int(re.search(r'α=(\d+)', bandpass).group(1))
        active = list(map(int, re.findall(r'A\((\d+)\)', bandpass)))
        self.assertEqual((N, alpha, active), (33, 16, [7, 8, 25, 26]))
        self.assertEqual(list(range(math.ceil(.4*N/2), math.floor(.5*N/2)+1)), [7, 8])
        A = [int(k in active) for k in range(N)]
        H = [value*cmath.exp(-2j*PI*k*alpha/N) for k, value in enumerate(A)]
        h = idft(H)
        factor_num, factor_den = map(int, re.search(r'h\(n\)=\((\d+)/(\d+)\)', bandpass).groups())
        paired = [factor_num/factor_den*(math.cos(14*PI*(n-alpha)/N)+math.cos(16*PI*(n-alpha)/N))
                  for n in range(N)]
        self.close(h, paired)
        self.close(h, list(reversed(h)))
        self.close([v.imag for v in h], [0]*N)
        self.assertAlmostEqual(paired[alpha], 4/33)
        self.close(dft(paired), H)
        wrong = [v/2 for v in paired]
        self.assertAlmostEqual(wrong[alpha], 2/33)
        for k in active:
            self.assertAlmostEqual(abs(dft(paired)[k]), 1)
            self.assertAlmostEqual(abs(dft(wrong)[k]), .5)
        self.assertIn('漏了因子2', bandpass)


if __name__ == '__main__':
    unittest.main(verbosity=2)
