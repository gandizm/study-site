'use strict';
// Zhong Shunshi, Electromagnetic Fields and Waves, 2nd ed., pp. 3-4, 59.
// These are the only two typography definitions. Legacy source is not rewritten.
const definitions = String.raw`\def\emvec#1{\overline{#1}}\def\emunit#1{\hat{#1}}`;

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

module.exports = { definitions, normalizeTex };
