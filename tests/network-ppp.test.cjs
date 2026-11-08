const assert=require('node:assert/strict');
const M=require('../site/network-ppp-models.js');
assert.equal(M.bytes('7D5EFE277D5D7D5D657D5E').output,'7EFE277D7D657E');
assert.equal(M.bytes('7d 23 00 fe').output,'0300FE');
assert.throws(()=>M.bytes('7D'));
assert.throws(()=>M.bytes('AZ'));
assert.throws(()=>M.bytes('123'));
assert.equal(M.bits('0110111111111100','add').output,'011011111011111000');
assert.equal(M.bits('0001110111110111110110','remove').output,'00011101111111111110');
assert.equal(M.bits('111110','add').output,'1111100');
assert.equal(M.bits('11111','add').output,'111110');
assert.equal(M.bits('1111100','remove').output,'111110');
assert.throws(()=>M.bits('111111','remove'));
assert.throws(()=>M.bits('11111','remove'));
for(let n=0;n<4096;n++){
  const raw=n.toString(2).padStart(12,'0'),stuffed=M.bits(raw,'add').output;
  assert.equal(M.bits(stuffed,'remove').output,raw);
  assert(!stuffed.includes('111111'));
}
assert.equal(M.utilization(480,8000,.04,1),.6);
const results=[1,7,127,255].map(w=>M.utilization(2000,1e6,.4,w));
results.forEach((v,i)=>assert(Math.abs(v-[1/201,7/201,127/201,1][i])<1e-12));
assert.equal(M.utilization(2000,1e6,.4,201),1);
assert(M.utilization(2000,1e6,.4,200)<1);
assert.deepEqual(M.windows.map(x=>x.s),[[0,1,2],[],[],[3],[1,2,3],[3],[3],[],[],[4,5,6]]);
assert.deepEqual(M.windows.map(x=>x.r),[[0,1,2],[0,1,2],[1,2],[1,2,3],[1,2,3],[1,2,3],[3],[3],[],[4,5,6]]);
console.log('PASS: six homework results; 4096 stuffing round trips; byte errors; utilization saturation; ten course-window states.');
