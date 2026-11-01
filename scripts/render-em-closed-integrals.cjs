#!/usr/bin/env node
'use strict';
// Build-time repair only. No MathJax runtime or CDN dependency is sent to readers.
// Install @mathjax/src@4.1.0 and @mathjax/mathjax-newcm-font@4.1.0 into a temporary
// prefix, then set NODE_PATH to that prefix's node_modules when running this file.
const fs = require('node:fs');
const path = require('node:path');
const {mathjax} = require('@mathjax/src/js/mathjax.js');
const {TeX} = require('@mathjax/src/js/input/tex.js');
const {SVG} = require('@mathjax/src/js/output/svg.js');
const {liteAdaptor} = require('@mathjax/src/js/adaptors/liteAdaptor.js');
const {RegisterHTMLHandler} = require('@mathjax/src/js/handlers/html.js');
require('@mathjax/src/js/util/asyncLoad/node.js');
require('@mathjax/src/js/input/tex/base/BaseConfiguration.js');
require('@mathjax/src/js/input/tex/ams/AmsConfiguration.js');

const adaptor = liteAdaptor();
RegisterHTMLHandler(adaptor);
const tex = new TeX({packages: ['base', 'ams'], formatError(_jax, error) {throw error;}});
const svg = new SVG({fontCache: 'none'});
const document = mathjax.document('', {InputJax: tex, OutputJax: svg});
const filename = path.join(__dirname, '../site/em-ch2-homework.html');
const source = fs.readFileSync(filename, 'utf8');
const decode = text => text.replace(/&quot;/g, '"').replace(/&#39;/g, "'").replace(/&lt;/g, '<').replace(/&gt;/g, '>').replace(/&amp;/g, '&');

(async () => {
  const pattern = /(<span class="hw-math[^>]*>)([\s\S]*?)(<\/span>)/g;
  let result = '', cursor = 0, count = 0;
  for (const match of source.matchAll(pattern)) {
    const opening = match[1];
    const attr = opening.match(/data-tex="([^"]*)"/);
    if (!attr || !attr[1].includes('\\oiint')) continue;
    const input = decode(attr[1]);
    const node = await document.convertPromise(input, {display: opening.includes('hw-math-display')});
    let output = adaptor.outerHTML(node);
    // The outer wrapper already supplies the unmodified accessible TeX label.
    output = output.replace('<svg ', '<svg aria-hidden="true" ');
    const expected = (input.match(/\\oiint(?![A-Za-z])/g) || []).length;
    const actual = (output.match(/<path\b[^>]*data-c="222F"/g) || []).length;
    if (actual !== expected || /data-mml-node="merror"|data-c="5C"|<text\b/.test(output)) {
      throw Error(`Non-vector or undefined-command fallback: ${input}`);
    }
    result += source.slice(cursor, match.index) + opening + output + match[3];
    cursor = match.index + match[0].length;
    count++;
  }
  if (count !== 6) throw Error(`Unexpected repair scope: ${count} expressions (expected 6)`);
  result += source.slice(cursor);
  fs.writeFileSync(filename, result);
  console.log(`Regenerated ${count} expressions with 7 native closed-double-integral SVG glyphs.`);
})().catch(error => {console.error(error); process.exitCode = 1;});
