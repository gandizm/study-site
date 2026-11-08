(function(root){
  'use strict';
  function bytes(raw){
    const s=String(raw).replace(/\s/g,'').toUpperCase();
    if(!s||s.length%2||!/^[0-9A-F]+$/.test(s))throw new Error('请输入偶数个十六进制字符，例如 7D5E。');
    const input=s.match(/../g), trace=[],out=[];
    for(let i=0;i<input.length;i++){
      const start=i;
      if(input[i]==='7D'){
        if(i+1>=input.length)throw new Error('最后一个 7D 后没有转义字节，数据不完整。');
        const next=input[++i], decoded=(parseInt(next,16)^0x20).toString(16).padStart(2,'0').toUpperCase();
        out.push(decoded);trace.push({start,end:i,read:'7D '+next,write:decoded,escaped:true,explain:'遇到转义字节 7D，与后一个字节一起处理；'+next+' 异或 20 → '+decoded+'。'});
      }else{
        out.push(input[i]);trace.push({start,end:i,read:input[i],write:input[i],escaped:false,explain:'没有遇到 7D，这个字节原样保留。'});
      }
    }
    return {input,trace,output:out.join('')};
  }
  function bits(raw,mode){
    const input=String(raw).replace(/\s/g,'');
    if(!input||!/^[01]+$/.test(input))throw new Error('只能输入 0 和 1。');
    let ones=0,out='',trace=[],tokens=[];
    for(let i=0;i<input.length;i++){
      const b=input[i];let extra='',deleted=false,explain;
      if(mode==='remove'&&ones===5){
        if(b!=='0')throw new Error('连续五个 1 后不是填充 0；请检查输入是否为已填充的数据区。');
        deleted=true;ones=0;explain='前面恰有连续五个 1：这个 0 是填充位，删除，并重新计数。';
      }else{
        out+=b;tokens.push({b,inserted:false});ones=b==='1'?ones+1:0;
        if(mode==='add'&&ones===5){out+='0';tokens.push({b:'0',inserted:true});extra='0';ones=0;explain='这使连续 1 达到五个：立即插入 0，再重新计数。';}
        else explain=b==='0'?'读到原有的 0：保留它，连续 1 计数归零。':'保留 1；连续 1 计数为 '+ones+'。';
      }
      trace.push({index:i,b,extra,deleted,ones,output:out,tokens:tokens.slice(),explain});
    }
    if(mode==='remove'&&ones===5)throw new Error('数据在五个连续 1 后结束，缺少应有的填充 0。');
    return{input,trace,output:out,tokens};
  }
  function utilization(L,R,rtt,W){return Math.min(1,W*(L/R)/(L/R+rtt));}
  const windows=[
    {label:'a · 初始态',s:[0,1,2],r:[0,1,2],pending:[],why:'双方各有三个编号的额度。还没有发送，也没有收到任何数据。'},
    {label:'b · 发送帧 0、1、2',s:[],r:[0,1,2],pending:[0,1,2],why:'发送方用完三份额度，发送扇区缩为空。接收方尚未收到帧，仍准备接收 0、1、2。'},
    {label:'c · 接收帧 0',s:[],r:[1,2],pending:[0,1,2],why:'接收方收到 0，接收下限从 0 移到 1。发送方还没有收到 ACK，所以它仍不能继续发。'},
    {label:'d · 接收 ACK0',s:[3],r:[1,2,3],pending:[1,2],why:'ACK0 确认到 0：发送上限扩出编号 3。按课件例图，接收方发 ACK0 时也已经恢复了一份额度，所以接收可用范围为 1、2、3。'},
    {label:'e · 接收 NAK1',s:[1,2,3],r:[1,2,3],pending:[1,2],why:'NAK1 要求从 1 回退重传。发送下限从 3 回到 1，重新允许发 1、2、3；其中 1、2 是待重传的旧帧，3 是尚未发送的新帧。'},
    {label:'f · 重传帧 1、2',s:[3],r:[1,2,3],pending:[1,2],why:'重新发送 1、2 后，下限再移到 3，只剩发 3 的额度。此时接收方还未收到这次重传。'},
    {label:'g · 接收帧 1、2',s:[3],r:[3],pending:[1,2],why:'接收方顺序收到 1、2，剩余接收额度只含 3。题目还没有给出它们的 ACK 到达，所以发送方状态不变。按本课示例，在下一给定确认事件前暂不补接收额度；接收额度是在接收方发出确认时补回，不是它“收到ACK”时补回。'},
    {label:'h · 发送帧 3',s:[],r:[3],pending:[1,2,3],why:'发送方用掉最后一份额度。接收方仍在等 3；发送方还有 1、2、3 尚未被确认。'},
    {label:'i · 接收帧 3',s:[],r:[],pending:[1,2,3],why:'接收方收到 3，也暂时用完额度。空着色区不是数据丢失，而是当前没有可继续使用的编号。'},
    {label:'j · 接收 ACK3',s:[4,5,6],r:[4,5,6],pending:[],why:'ACK3 累计确认到 3，未确认的 1、2、3 都得到确认。双方按课件画法恢复为 4、5、6 三份额度。'}
  ];
  const api={bytes,bits,utilization,windows};
  if(typeof module!=='undefined'&&module.exports)module.exports=api;
  else root.PPPLesson=api;
})(typeof globalThis!=='undefined'?globalThis:this);
