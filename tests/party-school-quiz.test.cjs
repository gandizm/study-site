const fs = require('fs');
const path = require('path');
const vm = require('vm');
const assert = require('assert');
const crypto = require('crypto');

const html = fs.readFileSync(path.join(__dirname, '../site/party-school-quiz.html'), 'utf8');
const payload = html.match(/<script id="question-data" type="application\/json">([\s\S]*?)<\/script>/)[1];
const data = JSON.parse(payload);
const code = html.match(/<script>\n([\s\S]*?)<\/script>/)[1];
const audit = JSON.parse(fs.readFileSync(path.join(__dirname, '../site/party-school-source-audit.json'), 'utf8'));
const KEY = 'party-school-quiz-135-v1';
const BACKUP = 'party-school-quiz-135-v1-before-306';
const digest = value => crypto.createHash('sha256').update(value).digest('hex');
const original135Digest = '7a35a1b0ebfecc526e7cd393b6efbdcf5c3e7a7323bc5ee7e58e73e56a2904f5';

function boot({store = {}, bank = data, preview = false, failRead = false, failWrite = () => false} = {}) {
  const elements = new Map(), reads = [], writes = [];
  const el = selector => {
    if (!elements.has(selector)) elements.set(selector, {
      textContent: selector === '#question-data' ? JSON.stringify(bank) : '',
      innerHTML: '', hidden: true, style: {},
      addEventListener() {}, focus() {}, classList: {toggle() {}},
      setAttribute() {}, toggleAttribute() {}
    });
    return elements.get(selector);
  };
  const sandbox = {
    console, Date, Math, Map, Set, JSON, Number, String, Array, Object, Error,
    setTimeout: () => 0, clearTimeout() {}, URLSearchParams,
    location: {search: preview ? '?preview=1' : ''},
    localStorage: {
      getItem(key) {
        reads.push(key);
        if (failRead) throw new Error('storage inaccessible');
        return Object.hasOwn(store, key) ? store[key] : null;
      },
      setItem(key, value) {
        if (failWrite(key)) throw new Error('quota');
        writes.push({key, value}); store[key] = value;
      },
      removeItem(key) { delete store[key]; }
    },
    window: {scrollTo() {}},
    document: {
      querySelector: el, querySelectorAll: () => [], getElementById: id => el('#' + id),
      body: {classList: {toggle() {}}}, activeElement: null, addEventListener() {}
    },
    assert
  };
  vm.createContext(sandbox); vm.runInContext(code, sandbox);
  return {store, reads, writes, el,
    run: source => vm.runInContext(source, sandbox),
    json: source => JSON.parse(vm.runInContext(`JSON.stringify(${source})`, sandbox))};
}

// The original 135 objects (including answer evidence and ambiguity labels) are immutable.
assert.equal(data.questions.length, 306);
assert.deepEqual(data.questions.map(q => q.number), Array.from({length: 306}, (_, i) => i + 1));
assert.equal(digest(JSON.stringify(data.questions.slice(0, 135))), original135Digest);
assert.deepEqual(data.questions.slice(0, 135).filter(q => q.status !== 'verified').map(q => q.number), [20, 27]);
for (const q of data.questions) {
  assert.equal(q.options.length, 3); assert(q.question.trim());
  if (q.status === 'verified') {
    assert(['A', 'B', 'C'].includes(q.answer)); assert(q.explanation && q.sources.length);
    assert(q.sources.every(s => s.title && /^https:\/\//.test(s.url)));
  } else assert.equal(q.answer, null);
}
assert.equal(audit.count, 306);
assert.equal(audit.verified_answer_count, data.questions.filter(q => q.status === 'verified').length);
assert.equal(audit.verified_answer_count, 298);
assert.equal(audit.legacy_verified_answer_count, 133);
assert.equal(audit.new_verified_answer_count, 165);
assert.deepEqual(audit.ungraded_questions, [20, 27, 142, 167, 266, 297, 301, 306]);
assert.deepEqual(audit.ungraded_questions, data.questions.filter(q => q.status !== 'verified').map(q => q.number));
assert.equal(audit.question_payload_sha256, digest(payload)); assert.equal(audit.original_answers_provided, false);
assert(html.includes("KEY='party-school-quiz-135-v1'")); assert(html.includes('study-global-nav'));
assert(html.includes('/study-site/party-school.html'));
assert(!/fetch\(|XMLHttpRequest|sendBeacon\(/.test(code)); new Function(code);
console.log('PASS: 306 questions, unchanged original 135 objects, evidenced grading, audit consistency, syntax and no answer uploads');

const app = boot();
app.run(`
const seen = new Set(), gradedCount = BANK.filter(q => q.status === 'verified').length;
for (let i = 0; i < BANK.length; i++) {
  const q = BY_ID.get(state.practice.order[state.practice.index]);
  assert(!seen.has(q.number)); seen.add(q.number); assert.equal(state.practice.index, i);
  next(); assert.equal(state.practice.index, i); answer(q.answer || 'A');
  const snap = JSON.stringify(state.total); answer('C'); assert.equal(JSON.stringify(state.total), snap); next();
}
assert.equal(state.practice.index, BANK.length); assert.equal(seen.size, BANK.length);
assert.equal(state.total.correct, gradedCount); assert.equal(state.total.wrong, 0);
assert.equal(state.total.pending, BANK.length - gradedCount); assert.equal(state.wrong.length, 0);
assert.equal(sessionStats(state.practice).accuracy, 100);
assert(document.querySelector('#main-content').innerHTML.includes('306 题，完整练过一遍。'));
startNew(); assert.equal(state.round, 2); assert.equal(state.practice.index, 0);
assert.equal(new Set(state.practice.order).size, 306); assert(validSavedState(state));
`);
for (const number of [1, 136]) {
  const test = boot();
  test.run(`
const q = BY_ID.get(${number}); assert.equal(q.status, 'verified');
state.practice.order = [q.number, ...BANK.filter(x => x.number !== q.number).map(x => x.number)];
answer(q.answer === 'A' ? 'B' : 'A'); assert.equal(state.wrong[0], q.number);
switchView('review'); assert.equal(state.review.order.length, 1);
answer(q.answer); assert.equal(state.wrong.length, 0); assert.equal(state.history[q.number].lastResult, 'correct');
next(); assert.equal(state.review.index, 1); assert(validSavedState(state));
`);
}
console.log('PASS: random round without repeats, answer lock, next gate, completion/restart, old/new wrong-answer mastery');

for (const q of data.questions.filter(q => q.status !== 'verified')) for (const choice of ['A', 'B', 'C']) {
  const test = boot();
  test.run(`
state.practice.order = [${q.number}, ...BANK.filter(q => q.number !== ${q.number}).map(q => q.number)]; render();
assert(document.querySelector('#main-content').innerHTML.includes('答案待核验')); answer('${choice}');
assert.equal(state.total.pending, 1); assert.equal(state.total.correct + state.total.wrong, 0);
assert.equal(state.wrong.length, 0); assert.equal(sessionStats(state.practice).accuracy, null);
assert.equal(state.history[${q.number}].lastResult, 'pending');
assert(!document.querySelector('#main-content').innerHTML.includes('class="option correct"'));
assert(!document.querySelector('#main-content').innerHTML.includes('class="option wrong"'));
assert(validSavedState(state));
`);
}
console.log('PASS: every unverified question and choice stays ungraded, outside wrong list and accuracy');

const legacyBank = {...data, questions: data.questions.slice(0, 135)};
function legacyFixture(kind) {
  const legacy = boot({bank: legacyBank}); legacy.run('state.practice.order = BANK.map(q => q.number); save()');
  if (['partial', 'answered', 'stats'].includes(kind)) {
    legacy.run("answer('B');next();answer('A');next();answer('B');next();");
    if (kind === 'answered') legacy.run("answer('C')");
    if (kind === 'stats') legacy.run("switchView('stats')");
  } else if (kind === 'complete') {
    legacy.run("while(state.practice.index < BANK.length){const q=BY_ID.get(state.practice.order[state.practice.index]);answer(q.answer||'A');next();}");
  } else if (kind === 'review' || kind === 'review-answered') {
    legacy.run("answer('A');next();answer('A');next();switchView('review');");
    if (kind === 'review-answered') legacy.run('answer(BY_ID.get(state.review.order[state.review.index]).answer)');
  }
  assert.equal(legacy.run('validSavedState(state)'), true); return legacy.store[KEY];
}
for (const kind of ['fresh', 'partial', 'answered', 'complete', 'review', 'review-answered', 'stats']) {
  const raw = legacyFixture(kind), before = JSON.parse(raw);
  const test = boot({store: {[KEY]: raw, unrelated_course_progress: 'do not touch'}}), after = test.json('state');
  assert.equal(test.run('storageBlocked'), false); assert.equal(test.run('validSavedState(state)'), true);
  assert.equal(after.practice.order.length, 306); assert.deepEqual(after.practice.order.slice(0, 135), before.practice.order);
  assert.deepEqual([...after.practice.order.slice(135)].sort((a, b) => a - b), Array.from({length: 171}, (_, i) => i + 136));
  const reduced = structuredClone(after); reduced.practice.order = reduced.practice.order.slice(0, 135); assert.deepEqual(reduced, before);
  assert.equal(test.store[BACKUP], raw); assert.equal(test.store.unrelated_course_progress, 'do not touch');
  assert.equal(test.writes[0].key, BACKUP); assert.equal(test.writes[1].key, KEY);
  const saved = test.store[KEY], reloaded = boot({store: test.store});
  assert.equal(reloaded.store[KEY], saved); assert.equal(reloaded.store[BACKUP], raw);
  assert.equal(reloaded.run('migrationApplied'), false); assert(!reloaded.writes.some(write => write.key === BACKUP));
}
console.log('PASS: fresh/partial/current-answered/completed/review/stats legacy migration preserves all fields, raw backup and idempotent reload');

const retainedBackup = boot({store: {[KEY]: legacyFixture('partial'), [BACKUP]: 'earlier original backup'}});
assert.equal(retainedBackup.store[BACKUP], 'earlier original backup'); assert.equal(retainedBackup.run('storageBlocked'), false);
const backupRaw = legacyFixture('answered');
const backupFailure = boot({store: {[KEY]: backupRaw}, failWrite: key => key === BACKUP});
assert.equal(backupFailure.store[KEY], backupRaw); assert.equal(backupFailure.run('storageBlocked'), true);
assert.equal(backupFailure.run('migrationBackupFailed'), true); assert.equal(backupFailure.run('state.practice.order.length'), 306);
assert.deepEqual(backupFailure.json('state.practice.answers'), JSON.parse(backupRaw).practice.answers);
backupFailure.run("next();answer('A');switchView('stats')"); assert.equal(backupFailure.store[KEY], backupRaw);
assert.equal(backupFailure.writes.length, 0); assert(backupFailure.el('#storage-notice').textContent.includes('未能备份'));
const mainFailure = boot({store: {[KEY]: backupRaw}, failWrite: key => key === KEY});
assert.equal(mainFailure.store[KEY], backupRaw); assert.equal(mainFailure.store[BACKUP], backupRaw);
assert.equal(mainFailure.run('storageOkay'), false);
console.log('PASS: backup-before-write, existing backup retention, backup/main-save failure protect original raw records');

for (const raw of ['{broken-json', ...[
  s => {s.practice.order.pop();}, s => {s.practice.order[1] = s.practice.order[0];},
  s => {s.practice.order[1] = 136;}, s => {s.practice.answers = {'1': {}};},
  s => {s.history = {'1': null};}, s => {s.total = [];}, s => {s.days = [];}, s => {s.wrong = [20];},
  s => {s.history['136'] = {attempts: 1, correct: 1, wrong: 0, pending: 0, lastResult: 'correct', lastChoice: 'B', lastAt: Date.now()};}
].map(mutate => {const s = JSON.parse(legacyFixture('fresh')); mutate(s); return JSON.stringify(s);})]) {
  const test = boot({store: {[KEY]: raw}}); test.run("answer('A');next();switchView('stats')");
  assert.equal(test.store[KEY], raw); assert.equal(test.writes.length, 0);
  assert.equal(test.el('#save-status').textContent, '已有记录受保护');
}
const preview = boot({store: {[KEY]: backupRaw}, preview: true}); preview.run("answer('A');next();switchView('stats')");
assert.equal(preview.reads.length, 0); assert.equal(preview.writes.length, 0); assert.equal(preview.store[KEY], backupRaw);
const inaccessible = boot({store: {[KEY]: backupRaw}, failRead: true});
assert.equal(inaccessible.writes.length, 0); assert.equal(inaccessible.store[KEY], backupRaw);
console.log('PASS: corrupt JSON/damaged nested legacy state protected, read-only preview and inaccessible storage');

const corrupt = boot({store: {[KEY]: '{broken'}}); corrupt.run('clearHistory()');
assert.equal(corrupt.run('storageBlocked'), false); assert.equal(JSON.parse(corrupt.store[KEY]).practice.order.length, 306);
assert.equal(corrupt.el('#save-status').textContent, '进度自动保存');
retainedBackup.run('clearHistory()'); assert(!Object.hasOwn(retainedBackup.store, BACKUP));
const cannotWrite = boot({store: {[KEY]: '{broken'}, failWrite: () => true}); cannotWrite.run('clearHistory()');
assert(cannotWrite.el('#toast').textContent.includes('无法保存')); assert(!cannotWrite.el('#toast').textContent.includes('已清空'));
const exact = app.store[KEY], restored = boot({store: {[KEY]: exact}});
assert.equal(restored.run('storageBlocked'), false); assert.equal(restored.store[KEY], exact);
console.log('PASS: explicit reset works, failed reset never claims success, current records restore exactly');
