/* Independent chapter reading record v1. Pure data functions, no credentials or network requests. */
const root=window;
(function(root){'use strict';
const COURSE='network-ch2-interfaces',VERSION=1,KEY='course-reading-network-ch2-interfaces-v1';
const CHAPTERS=[{"id":"network-ch2","title":"物理层 · 物理接口专题","pages":8,"startPage":27,"defaultPage":27}];
function fresh(){return {version:VERSION,course:COURSE,updatedAt:0,chapters:{},days:{},sessions:[],lastChapter:null};}
function chapter(s,id){if(!CHAPTERS.some(c=>c.id===id))throw Error('未知章节');return s.chapters[id]||(s.chapters[id]={lastPage:CHAPTERS.find(c=>c.id===id).defaultPage,pages:{}});}
function page(s,id,n){const c=CHAPTERS.find(c=>c.id===id);if(!c||!Number.isInteger(n)||n<c.startPage||n>=c.startPage+c.pages)throw Error('无效页码');const ch=chapter(s,id);return ch.pages[n]||(ch.pages[n]={ms:0,done:false,doneAt:0});}
function dateKey(t){const d=new Date(t);return d.getFullYear()+'-'+String(d.getMonth()+1).padStart(2,'0')+'-'+String(d.getDate()).padStart(2,'0');}
function credit(s,id,n,ms,end){if(!Number.isFinite(ms)||ms<=0)return;page(s,id,n).ms+=ms;let cursor=end-ms;while(cursor<end){const d=new Date(cursor),next=new Date(d.getFullYear(),d.getMonth(),d.getDate()+1).getTime(),until=Math.min(end,next);const key=dateKey(cursor);s.days[key]=(s.days[key]||0)+(until-cursor);cursor=until;}s.updatedAt=end;}
function mark(s,id,n,done,now){const p=page(s,id,n);p.done=done;p.doneAt=done?now:0;s.updatedAt=now;}
function markThrough(s,id,n,now){page(s,id,n);const changes=[];for(let i=CHAPTERS.find(c=>c.id===id).startPage;i<=n;i++){const p=page(s,id,i);if(!p.done){changes.push(i);mark(s,id,i,true,now);}}return {chapter:id,at:now,pages:changes};}
function undoThrough(s,record,now){let changed=0;for(const n of record.pages){const p=page(s,record.chapter,n);if(p.done&&p.doneAt===record.at){mark(s,record.chapter,n,false,now);changed++;}}return changed;}
function stats(s,id){const defs=id?CHAPTERS.filter(c=>c.id===id):CHAPTERS;let done=0,ms=0,total=0,timed=[];defs.forEach(c=>{total+=c.pages;Object.values(s.chapters[c.id]?.pages||{}).forEach(p=>{ms+=p.ms;if(p.done){done++;if(p.ms>=15000)timed.push(p.ms);}});});timed.sort((a,b)=>a-b);const median=timed.length?(timed[Math.floor((timed.length-1)/2)]+timed[Math.ceil((timed.length-1)/2)])/2:null;const enough=timed.length>=(id?3:5),left=total-done;return {done,total,ms,samples:timed.length,median,remaining:!left?0:enough?median*left:null,low:!left?0:enough?median*left*.7:null,high:!left?0:enough?median*left*1.3:null};}
function validate(input){
if(!input||input.version!==VERSION||input.course!==COURSE||typeof input.chapters!=='object'||!input.chapters||Array.isArray(input.chapters))throw Error('这不是本课程的有效进度备份');
const s=fresh(),num=(x,max)=>typeof x==='number'&&Number.isFinite(x)&&x>=0&&x<=max;
for(const [id,ch]of Object.entries(input.chapters)){const def=CHAPTERS.find(c=>c.id===id);if(!def||!ch||typeof ch.pages!=='object'||!ch.pages)throw Error('备份章节不匹配');const out=chapter(s,id);if(!Number.isInteger(ch.lastPage)||ch.lastPage<def.startPage||ch.lastPage>=def.startPage+def.pages)throw Error('备份页码无效');out.lastPage=ch.lastPage;for(const [n,p]of Object.entries(ch.pages)){if(!/^\d+$/.test(n)||!p||!num(p.ms,315360000000)||typeof p.done!=='boolean'||!num(p.doneAt,1e14))throw Error('备份记录无效');Object.assign(page(s,id,+n),{ms:p.ms,done:p.done,doneAt:p.done?p.doneAt:0});}}
if(!input.days||typeof input.days!=='object'||Array.isArray(input.days)||Object.keys(input.days).length>36600)throw Error('备份统计无效');for(const [day,ms]of Object.entries(input.days)){if(!/^\d{4}-\d{2}-\d{2}$/.test(day)||!num(ms,86400000))throw Error('备份日期或时长无效');s.days[day]=ms;}
if(!Array.isArray(input.sessions)||input.sessions.length>120)throw Error('备份学习记录无效');for(const x of input.sessions){if(!x||!num(x.start,1e14)||!num(x.end,1e14)||x.end<x.start||!num(x.ms,86400000*7)||!CHAPTERS.some(c=>c.id===x.chapter)||!Number.isInteger(x.done)||x.done<0||x.done>8)throw Error('备份计时记录无效');s.sessions.push({start:x.start,end:x.end,ms:x.ms,chapter:x.chapter,done:x.done});}
if(!num(input.updatedAt,1e14))throw Error('备份时间无效');s.updatedAt=input.updatedAt;s.lastChapter=CHAPTERS.some(c=>c.id===input.lastChapter)?input.lastChapter:null;return s;
}
const api={COURSE,VERSION,KEY,CHAPTERS,fresh,chapter,page,dateKey,credit,mark,markThrough,undoThrough,stats,validate};root.CourseProgressCore=api;
})(root);


