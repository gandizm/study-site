'use strict';
// Zhong Shunshi, Electromagnetic Fields and Waves, 2nd ed., pp. 3-4, 59.
// Shared by both build targets; angle/phasor marks and scalar averages are separate.
const definitions = String.raw`\def\emvec#1{\mathord{\mkern1.15mu\overline{\mkern-1.15mu#1\mkern-.2mu}\mkern.2mu}}\def\emunit#1{\hat{#1}}\def\emdiff#1{\overline{\mathrm d #1}}`;
const companionDefinitions = definitions;
function typesetTex(source) {
  // Retain the published homework's semantic labels for structured consumers.
  return source.replace(/\\emvec\{\\mathrm\s+d\s*([lA])\}/g, (_,symbol) => '\\emdiff{' + symbol + '}');
}

function normalizeTex(source) {
  // A hat already declares a unit vector: strip its legacy bold wrapper first.
  let tex = source.replace(/\\hat\s*\{\\(?:mathbf|boldsymbol)\s*(\\[a-zA-Z]+|[a-zA-Z])\s*\}/g, '\\emunit{$1}');
  // The textbook places the bar over the complete directed differential.
  tex = tex.replace(/\\mathrm\s+d\s*\\mathbf\s*([lA])/g, '\\emvec{\\mathrm d $1}');
  // In these two problems n denotes the outward UNIT normal, not a free vector.
  tex = tex.replace(/\\mathbf\s*(?:\{([a-zA-Z0-9])\}|([a-zA-Z0-9]))/g,
    (_match, braced, bare) => {
      const symbol = braced || bare;
      return `\\${symbol === 'n' ? 'emunit' : 'emvec'}{${symbol}}`;
    });
  if (/\\(?:mathbf|boldsymbol)\b/.test(tex)) throw new Error('Unmapped legacy vector notation: ' + source);
  return tex;
}

// Companion macros express semantics separately from the frozen two-problem release.
// Keep the short rule on the italic nucleus (never its subscript/prime); do not
// shorten a directed differential into a single-letter accent. A small rightward
// optical inset follows the ink, rather than extending to the whole advance width.
const bold = /\\(?:mathbf|boldsymbol)\s*(?:\{\s*(\\[A-Za-z]+|[A-Za-z0-9])\s*\}|(\\[A-Za-z]+|[A-Za-z0-9]))/g;
function companionTex(source) {
  let tex = source.replace(/\\hat\s*\{\s*\\(?:mathbf|boldsymbol)\s*(?:\{\s*(\\[A-Za-z]+|[A-Za-z0-9])\s*\}|(\\[A-Za-z]+|[A-Za-z0-9]))\s*\}/g,
    (_, a, b) => '\\emunit{' + (a || b) + '}');
  tex = tex.replace(/\\hat\s*(?:\{(\\[A-Za-z]+|[A-Za-z])\}|(\\[A-Za-z]+|[A-Za-z]))/g,
    (_, a, b) => '\\emunit{' + (a || b) + '}');
  // Printed p. 21: displacement d r has a bar on r alone. Printed pp. 57–59:
  // the directed line/area elements dl and ds take one bar across the whole object.
  tex = tex.replace(/(?:\\mathrm\s*(?:\{d\}|d)|(?<![\\A-Za-z])d)\s*(?:\\[,!]\s*)?\\(?:mathbf|boldsymbol)\s*(?:\{\s*(\\ell|[lsSaA])\s*\}|(\\ell(?![A-Za-z])|[lsSaA]))/g,
    (_, a, b) => '\\emdiff{' + (a || b) + '}');
  tex = tex.replace(bold, (_, a, b) => {
    const letter = a || b;
    if (letter === '0') return '0'; // Printed pp. 4, 21: the zero vector is written as plain 0.
    // In this seven-chapter corpus the only unadorned bold n denotes a unit
    // normal (boundary, outward conductor normal); scalar n is never matched.
    return '\\' + (letter === 'n' ? 'emunit' : 'emvec') + '{' + letter + '}';
  });
  if (/\\(?:mathbf|boldsymbol)\b/.test(tex)) throw Error('Unrecognized legacy vector: ' + source);
  return tex;
}
module.exports = { definitions, normalizeTex, typesetTex, companionDefinitions, companionTex };
