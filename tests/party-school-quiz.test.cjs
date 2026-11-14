const fs=require('fs'),vm=require('vm'),assert=require('assert');
const path=require('path');const html=fs.readFileSync(path.join(__dirname,'../site/party-school-quiz.html'),'utf8');const data=html.match(/<script id="question-data" type="application\/json">([\s\S]*?)<\/script>/)[1];const code=html.match(/<script>\n([\s\S]*?)<\/script>/)[1];
const els=new Map(),el=s=>{if(!els.has(s))els.set(s,{textContent:s==='#question-data'?data:'',innerHTML:'',hidden:true,style:{},addEventListener(){},focus(){},classList:{toggle(){}},setAttribute(){},toggleAttribute(){}});return els.get(s);};
const storage={};const sandbox={console,Date,Math,Map,Set,JSON,Number,String,Array,Object,Error,setTimeout,clearTimeout,URLSearchParams,location:{search:''},localStorage:{getItem:k=>storage[k]||null,setItem:(k,v)=>storage[k]=v},window:{scrollTo(){}},document:{querySelector:el,querySelectorAll:()=>[],getElementById:id=>el('#'+id),body:{classList:{toggle(){}}},activeElement:null,addEventListener(){}},assert};vm.createContext(sandbox);vm.runInContext(code,sandbox);
vm.runInContext(`
assert.equal(BANK.length,135);assert.equal(new Set(BANK.map(q=>q.number)).size,135);
assert.equal(BANK.filter(q=>q.status==='verified').length,133);assert.equal(BANK.filter(q=>q.status!=='verified').length,2);
const seen=new Set();for(let i=0;i<135;i++){const q=BY_ID.get(state.practice.order[state.practice.index]);assert(!seen.has(q.number));seen.add(q.number);assert.equal(state.practice.index,i);next();assert.equal(state.practice.index,i);answer(q.answer||'A');const snap=JSON.stringify(state.total);answer('C');assert.equal(JSON.stringify(state.total),snap);next();}
assert.equal(state.practice.index,135);assert.equal(state.total.correct,133);assert.equal(state.total.wrong,0);assert.equal(state.total.pending,2);assert.equal(state.wrong.length,0);assert.equal(sessionStats(state.practice).accuracy,100);assert.equal(seen.size,135);
startNew();assert.equal(state.round,2);assert.equal(state.practice.index,0);assert.equal(new Set(state.practice.order).size,135);
const testQ=BANK.find(q=>q.status==='verified');state.practice={order:[testQ.number,...BANK.filter(q=>q.number!==testQ.number).map(q=>q.number)],index:0,answers:{}};
answer(testQ.answer==='A'?'B':'A');assert.equal(state.wrong[0],testQ.number);switchView('review');assert.equal(state.review.order.length,1);answer(testQ.answer);assert.equal(state.wrong.length,0);assert.equal(state.history[testQ.number].lastResult,'correct');next();assert.equal(state.review.index,1);
console.log('PASS: 135 unique questions, 133 verified/2 ungraded, answer lock, next gate, round completion/restart, wrong collection/mastery, history, persistence');
`,sandbox);new Function(code);console.log('PASS: JavaScript syntax');

assert(html.includes('study-global-nav'));assert(html.includes('/study-site/party-school.html'));
const parsed=JSON.parse(data);assert.deepEqual(parsed.questions.filter(q=>q.status!=='verified').map(q=>q.number),[20,27]);
assert(html.includes("KEY='party-school-quiz-135-v1'"));assert(!/fetch\(|XMLHttpRequest|sendBeacon\(/.test(code));
const protectedStorage={'party-school-quiz-135-v1':'{broken-json'};let writes=0;
function context(search){return{...sandbox,location:{search},document:{...sandbox.document,querySelector:el,getElementById:id=>el('#'+id)},localStorage:{getItem:k=>protectedStorage[k]||null,setItem:(k,v)=>{writes++;protectedStorage[k]=v;}}};}
const preview=context('?preview=1');vm.createContext(preview);vm.runInContext(code,preview);vm.runInContext("answer('A');next();",preview);assert.equal(writes,0);assert.equal(protectedStorage['party-school-quiz-135-v1'],'{broken-json');
const corrupt=context('');vm.createContext(corrupt);vm.runInContext(code,corrupt);vm.runInContext("answer('A');next();",corrupt);assert.equal(writes,0);assert.equal(protectedStorage['party-school-quiz-135-v1'],'{broken-json');
console.log('PASS: subject navigation, unchanged grading boundaries, stable isolated storage, read-only preview, corrupt-record preservation');

// Explicit confirmed reset may replace a damaged record, but cannot report storage failure as success.
vm.runInContext('clearHistory()',corrupt);assert.equal(writes,1);assert.equal(JSON.parse(protectedStorage['party-school-quiz-135-v1']).schema,1);assert.equal(el('#save-status').textContent,'进度自动保存');
const cannotWrite=context('');cannotWrite.localStorage={getItem:()=>'{broken',setItem:()=>{throw new Error('quota')}};vm.createContext(cannotWrite);vm.runInContext(code,cannotWrite);vm.runInContext('clearHistory()',cannotWrite);assert(el('#toast').textContent.includes('无法保存'));assert(!el('#toast').textContent.includes('已清空'));
console.log('PASS: explicitly confirmed reset recovers corrupt storage; failed save never claims a successful clear');

// Well-formed JSON with damaged nested structures must be protected, not partially accepted.
for(const mutate of [s=>s.history={'1':null},s=>s.practice.answers={'1':{}},s=>s.total=[],s=>s.days=[],s=>s.wrong=[20]]){const broken=JSON.parse(vm.runInContext('JSON.stringify(freshState())',sandbox));mutate(broken);const raw=JSON.stringify(broken);let writes=0;const test={...sandbox,localStorage:{getItem:()=>raw,setItem:()=>writes++}};vm.createContext(test);vm.runInContext(code,test);vm.runInContext("switchView('stats');answer('A')",test);assert.equal(writes,0);assert.equal(el('#save-status').textContent,'已有记录受保护');}
const validRaw=vm.runInContext('JSON.stringify(state)',sandbox);const restored={...sandbox,localStorage:{getItem:()=>validRaw,setItem:()=>{}}};vm.createContext(restored);vm.runInContext(code,restored);assert.equal(vm.runInContext('storageBlocked',restored),false);assert.equal(vm.runInContext('JSON.stringify(state)',restored),validRaw);
console.log('PASS: nested state corruption protected; valid prior quiz records restore exactly');
