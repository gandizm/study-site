'use strict';
const assert=require('node:assert/strict');
const {neighborhoodModel}=require('../site/knowledge-neighborhood.js');
const map={nodes:Array.from({length:9},(_,i)=>({id:'n'+i,label:'节点'+i,pages:[i+1]})),edges:[
 {from:'n1',to:'n0',label:'先修'},{from:'n1',to:'n0',label:'构造'},
 {from:'n2',to:'n0',label:'对比'},{from:'n3',to:'n0',label:'先修'},{from:'n4',to:'n0',label:'先修'},
 {from:'n0',to:'n5',label:'应用'},{from:'n0',to:'n6',label:'检验'},{from:'n0',to:'n7',label:'拓展'},{from:'n0',to:'n8',label:'对比'}]};
const desktop=neighborhoodModel(map,'n0',3);
assert.equal(desktop.current.id,'n0');assert.equal(desktop.incoming.length,3);assert.equal(desktop.incomingTotal,4);assert.equal(desktop.outgoing.length,3);assert.equal(desktop.outgoingTotal,4);
assert.deepEqual(desktop.incoming[0].labels,['先修','构造']);
const compact=neighborhoodModel(map,'n0',1);assert.equal(compact.incoming.length,1);assert.equal(compact.outgoing.length,1);assert.equal(compact.incomingTotal,4);
const leaf=neighborhoodModel(map,'n8',3);assert.equal(leaf.incoming[0].node.id,'n0');assert.equal(leaf.outgoingTotal,0);
assert.equal(neighborhoodModel(map,'missing',3).current.id,'n0');
assert.equal(neighborhoodModel(map,'n0',100).incoming.length,3);
console.log('Neighborhood model passed: correct directed edges, multiple-label deduplication, 3-node desktop cap, 1-node compact cap, honest full counts, real page links and leaf/root handling.');
