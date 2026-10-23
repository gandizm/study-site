'use strict';
const assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path');
const {validateKnowledgeMap}=require('../site/knowledge-map.js');
const {neighborhoodModel}=require('../site/knowledge-neighborhood.js');
const site=process.env.STUDY_SITE_ROOT ? path.join(process.env.STUDY_SITE_ROOT,'site') : path.resolve(__dirname,'../site');
let pagesTotal=0,nodesTotal=0,edgesTotal=0;
const registry=JSON.parse(fs.readFileSync(path.join(site,'knowledge-map-registry.json'),'utf8'));
for(const {chapterId:id,readerPath:reader,readerPageCount:total} of registry.maps){
 const html=fs.readFileSync(path.join(site,reader),'utf8');
 const pages=[...html.matchAll(/<article\b[^>]*class="[^"]*slide-page[^>]*data-page="(\d+)"/g)].map(match=>Number(match[1]));
 assert.equal(pages.length,total);assert.equal(new Set(pages).size,total);
 let graphFile=path.join(site,'courses',id,'knowledge-map.json');
 const graph=validateKnowledgeMap(JSON.parse(fs.readFileSync(graphFile,'utf8')),pages);
 assert.deepEqual(graph.missingPages,[]);assert.equal(graph.coveredPages.length,total);
 for(const node of graph.nodes)for(const limit of [1,3]){
  const model=neighborhoodModel(graph,node.id,limit);assert.equal(model.current.id,node.id);
  assert.ok(model.incoming.length<=limit);assert.ok(model.outgoing.length<=limit);
  assert.equal(model.incomingTotal,new Set(graph.edges.filter(edge=>edge.to===node.id).map(edge=>edge.from)).size);
  assert.equal(model.outgoingTotal,new Set(graph.edges.filter(edge=>edge.from===node.id).map(edge=>edge.to)).size);
  for(const related of [...model.incoming,...model.outgoing])assert.ok(related.node.pages.every(page=>pages.includes(page)));
 }
 pagesTotal+=pages.length;nodesTotal+=graph.nodes.length;edgesTotal+=graph.edges.length;
 console.log(`${id}: ${graph.nodes.length} nodes, ${graph.edges.length} directed relations, ${pages.length}/${total} real pages PASS`);
}
const good={version:1,nodes:[{id:'a',label:'A',pages:[103]},{id:'b',label:'B',pages:[104],prerequisites:['a'],anchors:{104:'detail-104'}}]};
assert.deepEqual(validateKnowledgeMap(good,[103,104]).missingPages,[]);
assert.deepEqual(validateKnowledgeMap(good,[103,104,105]).missingPages,[105]);
for(const change of [
 data=>{data.version=2;},data=>{data.nodes=[];},data=>{data.nodes[1].id='a';},data=>{data.nodes[0].label='';},
 data=>{data.nodes[0].pages=[1];},data=>{data.nodes[0].pages=['103'];},data=>{data.nodes[0].pages=[103,103];},
 data=>{data.nodes[1].prerequisites=['missing'];},data=>{data.nodes[1].prerequisites=['b'];},
 data=>{data.edges=[{from:'a',to:'missing',label:'invalid'}];},data=>{data.edges=[{from:'a',to:'b',label:''}];},
 data=>{data.nodes[1].anchors={105:'wrong-page'};},data=>{data.nodes[1].anchor=4;}
]){const invalid=structuredClone(good);change(invalid);assert.throws(()=>validateKnowledgeMap(invalid,[103,104]));}
console.log(JSON.stringify({newRecoveryCore:true,chapters:registry.maps.length,pages:pagesTotal,nodes:nodesTotal,relations:edgesTotal,invalidCases:13,browserGeometry:'not tested'},null,2));
