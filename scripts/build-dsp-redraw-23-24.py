#!/usr/bin/env python3
"""Build reviewed Ch 2.3/2.4 two-pass lessons and mathematical SVGs.
MathML is reused from the existing local, reviewed textbook companion; no CDN.
Run from repo root. Numerical inputs embedded in SVG metadata are tested separately.
"""
from pathlib import Path
from lxml import html, etree
import math, cmath, json, re, hashlib
from html import escape
ROOT=Path(__file__).resolve().parents[1]; OUT=ROOT/'site/dsp-redraw'; AS=OUT/'assets'
OUT.mkdir(exist_ok=True);AS.mkdir(exist_ok=True)
FORM=[]
for p in sorted((ROOT/'site/dsp-textbook').glob('*.html')):
    doc=html.fromstring(p.read_text())
    for el in doc.xpath('//*[@data-latex]'):
        children=el.xpath('./math')
        if children: FORM.append((re.sub(r'\s+','',el.get('data-latex')),etree.tostring(children[0],encoding='unicode',method='html')))
def F(prefix):
    key=re.sub(r'\s+','',prefix)
    found=[(k,v) for k,v in FORM if k.startswith(key)]
    if not found: raise ValueError('Missing reviewed formula: '+prefix)
    k,v=min(found,key=lambda x:len(x[0])); v=re.sub('display="inline"','display="block"',v)
    return '<div class="formula">'+v+'</div>'
def m(s,label):return '<div class="formula"><math xmlns="http://www.w3.org/1998/Math/MathML" display="block" aria-label="'+escape(label,quote=True)+'"><mrow>'+s+'</mrow></math></div>'
def safe(s):
    # Authored prose is text; allow only our explicit inline formatting tags.
    out=escape(str(s),quote=False)
    return re.sub(r'&lt;(/?(?:strong|em|sub|sup|code))&gt;',r'<\1>',out)
def P(s):return '<p>'+safe(s)+'</p>'
def UL(xs):return '<ul>'+''.join('<li>'+safe(x)+'</li>' for x in xs)+'</ul>'
def T(head,rows):return '<div class="table-wrap"><table><thead><tr>'+''.join('<th scope="col">'+safe(x)+'</th>' for x in head)+'</tr></thead><tbody>'+''.join('<tr>'+''.join('<td>'+safe(x)+'</td>' for x in row)+'</tr>' for row in rows)+'</tbody></table></div>'
def fig(name,alt,caption):return {'src':'dsp-redraw/assets/'+name+'.svg','alt':alt,'caption':caption}
def card(id,title,pages,body,level='essential',figure=None,pitfall=None,check=None):
    d={'id':id,'title':title,'level':level,'sourcePages':pages,'bodyHtml':body}
    if figure:d['figure']=figure
    if pitfall:d['pitfall']=pitfall
    if check:d['check']={'question':check[0],'answerHtml':P(check[1])}
    return d
# Scientific figures: generous 24px labels; no rasterized equations.
BLUE='#155eaa'; TEAL='#087f79'; ORANGE='#b45412'; INK='#16314a'; MUTED='#577082'; GRID='#d9e4eb'
def tx(x,y,s,size=24,fill=INK,anchor='start',weight=400):return f'<text x="{x}" y="{y}" font-size="{size}" fill="{fill}" text-anchor="{anchor}" font-weight="{weight}">{escape(str(s))}</text>'
def line(x1,y1,x2,y2,color=GRID,width=2,dash=''):return f'<line x1="{x1:.2f}" y1="{y1:.2f}" x2="{x2:.2f}" y2="{y2:.2f}" stroke="{color}" stroke-width="{width}"'+(f' stroke-dasharray="{dash}"' if dash else '')+'/>'
def circle(x,y,r=5,color=BLUE):return f'<circle cx="{x:.2f}" cy="{y:.2f}" r="{r}" fill="{color}"/>'
def svg(name,title,desc,content,height=460,metadata=None):
    text=f'<svg xmlns="http://www.w3.org/2000/svg" width="960" height="{height}" viewBox="0 0 960 {height}" role="img" aria-labelledby="title desc"><title id="title">{escape(title)}</title><desc id="desc">{escape(desc)}</desc><metadata>{escape(json.dumps(metadata or {},ensure_ascii=False))}</metadata><rect width="960" height="{height}" fill="#fbfdff"/><g font-family="system-ui, Noto Sans CJK SC, sans-serif">{content}</g></svg>'
    (AS/(name+'.svg')).write_text(text)
def stem(values,x=80,y=210,w=790,h=120,color=BLUE,maxv=None,labels=True,start=0):
    hi=maxv or max(max(values),1); pitch=w/max(len(values),2); out=line(x-20,y,x+w,y,INK)
    for i,v in enumerate(values):
        xx=x+i*pitch;yy=y-v/hi*h;out+=line(xx,y,xx,yy,color,3)+circle(xx,yy,5,color)
        if labels:out+=tx(xx,y+30,i+start,20,MUTED,'middle')+tx(xx,yy-12,f'{v:g}',22,color,'middle')
    return out+tx(x+w+16,y+30,'n',22,MUTED)
# Unit circle: z uses + exponent; W uses - exponent.
s='';cx,cy,rad=240,245,150
s+=line(60,cy,430,cy,GRID)+line(cx,65,cx,425,GRID)+f'<circle cx="{cx}" cy="{cy}" r="{rad}" fill="none" stroke="{GRID}" stroke-width="3"/>'
for k in range(8):
 a=2*math.pi*k/8;xx=cx+rad*math.cos(a);yy=cy-rad*math.sin(a);s+=circle(xx,yy,7,BLUE)+tx(cx+(rad+35)*math.cos(a),cy-(rad+35)*math.sin(a)+8,str(k),24,BLUE,'middle')
s+=tx(520,100,'同一组 N 个频率位置',30,INK,weight=700)+tx(520,158,'ωₖ = 2πk / N',30,BLUE)+tx(520,213,'zₖ = exp(+j2πk / N)',28,BLUE)+tx(520,278,'zₖ⁻ⁿ = exp(−j2πkn / N)',26,INK)+tx(520,338,'W_N = exp(−j2π / N)',26,TEAL)+tx(520,394,'例：N = 8；从 k = 0 逆时针走',22,MUTED)
svg('23-unit-circle','DFT取样位置与旋转因子的正负号','八个Z平面取样点逆时针排列；正变换内部z的负幂给负指数。',s,470,{'N':8,'angles':[2*math.pi*k/8 for k in range(8)]})
# Rectangle spectrum with 8 and 16 samples, same curve.
s=tx(45,40,'同一条 DTFT，换两种频率网格',30,INK,weight=700)
samples={}
for row,N in enumerate((8,16)):
 y0=230+row*245;x0=75;w=800;h=140
 s+=tx(45,y0-h-15,f'N = {N}   |X|',25,BLUE)+line(x0,y0,x0+w,y0,INK)
 for val in (0,2,4):s+=line(x0,y0-h*val/4,x0+w,y0-h*val/4,GRID)+tx(53,y0-h*val/4+7,val,20,MUTED,'end')
 pts=[]
 for i in range(501):
  om=2*math.pi*i/500;v=abs(sum(cmath.exp(-1j*om*n) for n in range(4)));pts.append(f'{x0+w*i/500:.2f},{y0-h*v/4:.2f}')
 s+=f'<polyline points="{" ".join(pts)}" fill="none" stroke="{TEAL}" stroke-width="3"/>'
 vals=[]
 for k in range(N):
  v=abs(sum(cmath.exp(-2j*math.pi*k*n/N) for n in range(4)));vals.append(v);xx=x0+w*k/N;yy=y0-h*v/4;s+=line(xx,y0,xx,yy,BLUE,2)+circle(xx,yy,5,BLUE)
 for p,t in [(0,'0'),(.5,'π'),(1,'2π')]:s+=tx(x0+w*p,y0+28,t,22,MUTED,'middle')
 s+=tx(915,y0+28,'ω',24,MUTED)
 samples[str(N)]=vals
s+=tx(70,535,'曲线不变；16 点中的偶数频点 = 8 点的原频点',24,INK)
svg('23-rectangle-samples','四点矩形序列的8点与16点DFT','曲线由四个复指数的有限和计算，蓝色样点分别为8点与16点DFT幅度。',s,570,{'sequence':[1,1,1,1],'magnitudes':samples})
# Circular movement preserves explicit indices.
s=tx(45,42,'先固定 N，再把下标绕回 0 … N−1',30,INK,weight=700)
for row,(title,vals) in enumerate([('原数组，N = 5',[2,1,3,1,.5]),('左移 1：读取 (n+1) mod 5',[1,3,1,.5,2]),('右移 2：读取 (n−2) mod 5',[1,.5,2,1,3])]):
 y=185+row*180;s+=tx(45,y-105,title,25,INK)+stem(vals,100,y,760,65,BLUE,3)
s+=tx(45,610,'改成 N = 6：先加一个 0，之后才做六点圆周操作。',24,ORANGE)
svg('23-circular-shift','原课件五点数组的左右圆周移位','原数组2、1、3、1、0.5，左移一格及右移两格后保持五点且下标从零开始。',s,645,{'original':[2,1,3,1,.5],'left1':[1,3,1,.5,2],'right2':[1,.5,2,1,3]})
# Convolution wrap, colors show tail addends.
ylin=[1,4,8,10,8,4,1];s=tx(45,42,'线性结果折回相加，得到圆周结果',30,INK,weight=700)
s+=tx(45,92,'线性自卷积：长 4 + 4 − 1 = 7',25,INK)+stem(ylin,90,260,790,125,BLUE,10)
s+=tx(45,335,'N = 4：n = 4、5、6 分别折回 0、1、2',24,ORANGE)+stem([9,8,9,10],90,500,790,125,TEAL,10)
s+=tx(90,565,'9 = 1+8',24,TEAL)+tx(290,565,'8 = 4+4',24,TEAL)+tx(490,565,'9 = 8+1',24,TEAL)+tx(690,565,'10 不变',24,TEAL)
svg('23-convolution-fold','四点数组自卷积的时域折回','线性结果1 4 8 10 8 4 1；四点圆周卷积为9 8 9 10。',s,605,{'input':[1,2,2,1],'linear':ylin,'circular4':[9,8,9,10]})
# DFT real symmetry explicit values.
s=tx(45,42,'实序列 → 频谱成对共轭，而非全实',30,INK,weight=700)+tx(45,91,'x = [1, 2, 0, 0]；X = [3, 1−2j, −1, 1+2j]',26,INK)
vals=['3','1−2j','−1','1+2j']
for i,v in enumerate(vals):
 x=140+210*i;s+=circle(x,210,43,BLUE if i in [1,3] else TEAL)+tx(x,218,str(i),27,'white','middle')+tx(x,297,v,28,INK,'middle')
s+=line(350,150,770,150,BLUE,3)+line(350,150,350,165,BLUE,3)+line(770,150,770,165,BLUE,3)+tx(560,134,'共轭配对',25,BLUE,'middle')+tx(140,365,'k = 0 自配对',23,TEAL,'middle')+tx(560,365,'k = N/2 自配对',23,TEAL,'middle')+tx(45,420,'自配对频点必为实数；实数可以是负数，也不必是 0。',24,MUTED)
svg('23-real-symmetry','四点实序列的频谱共轭配对','频点1与3互为共轭；0和2与自己配对，频谱值为实数。',s,460,{'input':[1,2,0,0],'dft':[[3,0],[1,-2],[-1,0],[1,2]]})
# Frequency sampling rectangular folding N 3,4,5,6.
s=tx(45,42,'五个 1，按余数分组后相加',30,INK,weight=700)
folds={}
for row,N in enumerate((3,4,5,6)):
 vals=[sum(1 for n in range(5) if n%N==k) for k in range(N)];folds[str(N)]=vals;y=180+row*175
 s+=tx(45,y-110,f'N = {N}：'+('发生时域混叠' if N<5 else '无混叠'),25,ORANGE if N<5 else TEAL)+stem(vals,120,y,700,65,ORANGE if N<5 else TEAL,2)
s+=tx(45,800,'比较的是同一原序列的 DTFT 样点，不是把原序列截成 N 点。',23,INK)
svg('24-rectangle-fold','五点矩形序列的四种频域采样结果','三点为2 2 1；四点为2 1 1 1；五点全1；六点最后补0。',s,840,{'input':[1,1,1,1,1],'folds':folds})
# Time residue map, one example sufficient.
s=tx(45,42,'频率取 N 点 ↔ 时间相隔 N 的值相加',30,INK,weight=700)
for i in range(5):
 xx=100+i*170;s+=circle(xx,135,30,BLUE)+tx(xx,143,'1',24,'white','middle')+tx(xx,190,'n='+str(i),22,MUTED,'middle')
for i,v in enumerate([2,1,1,1]):
 xx=100+i*170;s+=circle(xx,375,35,TEAL)+tx(xx,383,str(v),28,'white','middle')+tx(xx,433,'余数 '+str(i),22,MUTED,'middle')
for i in range(4):s+=line(100+i*170,210,100+i*170,325,GRID,3)
s+=f'<path d="M 780 210 C 780 280 100 270 100 325" fill="none" stroke="{ORANGE}" stroke-width="4"/>'+tx(470,240,'4 mod 4 = 0',26,ORANGE,'middle')+tx(45,488,'同一盒只留下和：2 = 1+1，无法知道原来各占多少。',25,INK)
svg('24-residue-fold','四点采样把第零与第四个样值相加','五个样值各为1，索引4绕回余数0，因此四点IDFT首项为2。',s,530,{'N':4,'assignments':[0,1,2,3,0],'output':[2,1,1,1]})
# Exponential same comparison domain = first 10 samples, not periodic full curve.
s=tx(45,42,'无限长指数：更多频点减小折回尾巴',30,INK,weight=700)+tx(45,85,'a = 0.8；这里只比较主值区间的前 10 点',24,MUTED)
y0=370;x0=80;w=780;h=220
s+=line(x0-20,y0,x0+w,y0,INK)
for v in (0,.5,1,1.2):s+=line(x0-20,y0-h*v/1.3,x0+w,y0-h*v/1.3,GRID)+tx(55,y0-h*v/1.3+7,v,20,MUTED,'end')
for vals,color in [([.8**n for n in range(10)],INK),([.8**n/(1-.8**10) for n in range(10)],ORANGE),([.8**n/(1-.8**40) for n in range(10)],TEAL)]:
 pts=[]
 for i,v in enumerate(vals):
  xx=x0+w*i/10;yy=y0-h*v/1.3;pts.append(f'{xx},{yy}');s+=circle(xx,yy,5,color)
 s+=f'<polyline points="{" ".join(pts)}" fill="none" stroke="{color}" stroke-width="2.5"/>'
for i in range(10):s+=tx(x0+w*i/10,y0+30,i,20,MUTED,'middle')
s+=tx(80,455,'● 原序列',24,INK)+tx(330,455,'● N=10：高约12.03%',24,ORANGE)+tx(80,505,'● N=40：高约0.0133%，几乎重合',24,TEAL)
svg('24-exponential-fold','无限长指数在十点和四十点频域采样后的误差','主值范围内折叠值为0.8的n次方除以1减0.8的N次方。N40与原序列几乎重合但并非完全相等。',s,550,{'a':.8,'N':[10,40],'relativeErrors':[.8**N/(1-.8**N) for N in (10,40)]})
# Minimal, fully typeset core transform pair.
W=m('<msub><mi>W</mi><mi>N</mi></msub><mo>=</mo><msup><mi>e</mi><mrow><mo>−</mo><mi>j</mi><mn>2</mn><mi>π</mi><mo>/</mo><mi>N</mi></mrow></msup>','W_N = exp(−j 2π/N)')
sum_n='<munderover><mo>∑</mo><mrow><mi>n</mi><mo>=</mo><mn>0</mn></mrow><mrow><mi>N</mi><mo>−</mo><mn>1</mn></mrow></munderover>'
sum_k=sum_n.replace('<mi>n</mi>','<mi>k</mi>')
dft=m('<mi>X</mi><mo>(</mo><mi>k</mi><mo>)</mo><mo>=</mo>'+sum_n+'<mi>x</mi><mo>(</mo><mi>n</mi><mo>)</mo><msubsup><mi>W</mi><mi>N</mi><mrow><mi>k</mi><mi>n</mi></mrow></msubsup>','X(k) = sum from n=0 to N−1 of x(n) W_N^(kn)')
idft=m('<mi>x</mi><mo>(</mo><mi>n</mi><mo>)</mo><mo>=</mo><mfrac><mn>1</mn><mi>N</mi></mfrac>'+sum_k+'<mi>X</mi><mo>(</mo><mi>k</mi><mo>)</mo><msubsup><mi>W</mi><mi>N</mi><mrow><mo>−</mo><mi>k</mi><mi>n</mi></mrow></msubsup>','x(n) = 1/N times sum from k=0 to N−1 of X(k) W_N^(−kn)')
c=[]
c.append(card('dft-definition','DFT：N 个时间值，换成 N 个频率值',list(range(1,6)),P('DFT 处理有限数组，不要求真实信号周期重复。先选点数 N；不足 N 点就在末尾补零。n 是时间位置，k 是频点编号，都取 0 到 N−1。')+W+dft+idft+P('正变换的指数为负；逆变换为正，并除以 N。两式可互相恢复，前提是保留完整复数值，不只留幅度。'),check=('两点数组 [a,b] 的 DFT 是什么？','[a+b, a−b]；相加与相减后各除以2，便恢复 a、b。')))
c.append(card('sampling-relations','DFT 采的是 DTFT 上的哪些点',list(range(6,14)),P('把数组区间外设为零，就有一条连续的 DTFT 曲线；DFT 每隔 2π/N 取一个复数值。')+F(r'X(k)=X(e^{j\omega})\big|')+P('原例 x=R₄(n)=[1,1,1,1]：8点与16点DFT采同一条曲线，直流值都是4。补零只加密频率网格，不新增观测，也不自动提高分辨能力。')+P('Z 变换取样位置是正指数 z=eʲ²πᵏ⁄ᴺ。若将数组周期延拓，课件的未归一化 DFS 系数等于 X(k)；若合成式不带1/N，其系数则是 X(k)/N。单位脉冲的任意 N 点DFT均为 N 个1。'),figure=fig('23-rectangle-samples','四个1的DTFT幅度曲线及8点、16点DFT样点','线是连续频率曲线，点是有限频率样本；横轴是 ω，不是 k。'),pitfall='DFT数组在 n、k 上的隐含周期是 N；DTFT对 ω 的周期是2π，不能混用单位。'))
c.append(card('circular-index','圆周移位：从一端出去，从另一端回来',list(range(14,20)),P('主值区间选0…N−1。下标 mod N 是“取余数”，不是对样值取模。课件用加号表示左移：')+F(r'y[n]=x[(n+m)\bmod N]')+P('原数组 [2,1,3,1,0.5] 先选 N=5。左移1得到 [1,3,1,0.5,2]；右移2得到 [1,0.5,2,1,3]。若 N=6，应先补0再移，不能最后随便加0。'),figure=fig('23-circular-shift','五点原数组、左移一格、右移两格的重绘','圆周翻转的下标顺序是0,N−1,…,1，不是把整个数组倒排。'),pitfall='原P15的自由索引混写。这里统一用 n 作时间位置、r 作周期副本编号。'))
c.append(card('two-convolutions','线性卷积与圆周卷积，差在边界',list(range(20,26)),P('线性卷积不绕回。长 L、M 的两段序列，结果最多占 L+M−1 个位置。N 点圆周卷积则把下标绕回同一个 N 点环：')+F(r'y_N[n]=\sum')+P('手算按“圆周翻转→移到输出位置→逐点乘→相加”。也可先算线性结果，再把相隔 N 的项相加。若要用圆周卷积获得完整线性结果，先将两输入补零至 N≥L+M−1。'),figure=fig('23-convolution-fold','原四点课堂例的线性结果与四点圆周折回','两条输入都必须使用同一个 N；仅 N≥max(L,M) 不保证没有时域混叠。')))
c.append(card('shift-properties','移位看指数正负号，不靠口诀',[26,27,28,29,30,31],P('性质都针对同一个 N。线性：输入加权相加，DFT也加权相加。时间左移 m，与频率左移 l 分别是：')+F(r'x_m(n)=x((n+m))_N')+F(r'y(n)=W_N^{ln}x(n)')+P('第一式：时间左移，频谱乘正指数，相位改变但幅度不变。第二式：时间乘负指数，频谱变为 X((k+l))<sub>N</sub>。判断方向时，问“原第0点会跑到哪里”。'),check=('右移 n₀ 点时，频谱乘什么？','乘 exp(−j2πkn₀/N)=W_N^(kn₀)。右移的下标是 n−n₀，不是 n+n₀。')))
c.append(card('multiplication-convolution','频谱相乘，得到的是圆周卷积',[32,33,34],F(r'y(n)=\sum_{m=0}^{N-1}x_1(m)x_2')+P('这就是“DFT→频谱逐点乘→IDFT”的计算链。要算线性卷积，先按上一卡补足零。反过来，时间逐点相乘，对应频率 N 点圆周卷积再除以 N。'),pitfall='两个方向尺度不同：时间圆周卷积↔频率乘；时间乘↔频率圆周卷积/N。'))
c.append(card('conjugate-energy','共轭与能量：两条快速验算规则',list(range(35,40)),F(r'\operatorname{DFT}\{x^*(n)\}')+F(r'\sum_{n=0}^{N-1}|x(n)|^2')+P('星号表示复共轭；−k 按 N 取模，k=0仍回到0。原P39的首个求和指标与项中变量混写，这里统一用n。能量用平方模；正变换不归一化时，频域平方模之和必须除以 N。'),check=('x=[1,1,1,1]，X=[4,0,0,0]，能量是否吻合？','时间能量4；频率能量16除以N=4，也为4。')))
c.append(card('real-symmetry','实信号的频谱为什么只需看一半',[40,41,42,43,44,45,46,47,48,49,50,51,52,53],P('实数组满足 X(k)=X*((−k) mod N)：成对频点互为共轭。于是实部偶对称、虚部奇对称、幅度偶对称；非零点的相位在模2π意义下反号。')+P('0点自配对；N为偶数时N/2点也自配对，所以这些频点为实数。一般实数组的其他频点仍可为复数。纯虚数组则满足 X(k)=−X*((−k) mod N)，不要照抄实数组结论。'),figure=fig('23-real-symmetry','实数组四点DFT共轭配对示意','完整的共轭偶/奇分解与两条实序列分离，放在第二遍。'),pitfall='零点没有确定相位；π与−π是同一角度，不能把显示分支跳变当成数学关系失效。'))
# Optional second pass. Proof pages remain explicitly mapped rather than disappearing.
c.append(card('inverse-proof','为什么 IDFT 能恢复每个样值',[5],P('固定要恢复的位置 n，另用 m 遍历输入；k 遍历频点。把DFT代入IDFT，关键只剩单位根的有限和：')+F(r'\sum_{k=0}^{N-1}W_N^{k(m-n)}=')+P('m、n都在同一主值区间时，同余就是相等。只有 m=n 留下 N·x(n)，再除以N即得x(n)。其他情况用等比和：(1−qᴺ)/(1−q)=0。'),level='deep'))
c.append(card('rectangle-details','原 R₄ 例：8点、16点与可去奇点',[7,8,9,10,11,12,13],F(r'X(e^{j\omega})=\sum_{n=0}^{3}')+P('先有限求和，再代 ω=2πk/N。ω为2π的整数倍时，回到四项相加，值为4，不计算0/0。')+F(r'X_8(k)=')+F(r'X_{16}(k)=')+P('8点完整结果为 [4,1−j(1+√2),0,1−j(√2−1),0,1+j(√2−1),0,1+j(1+√2)]。16点结果满足 X₁₆(2k)=X₈(k)，其余点代同一有限和；不另背16个数。')+F(r'X(k+N)=')+P('逆式延到所有整数n也按N重复，但这不是区间外补零的原有限序列。'),level='deep',figure=fig('23-unit-circle','八个Z平面采样点以及正负指数区别','正指数选取样位置；z的负幂产生DFT的负指数。')))
c.append(card('periodization-correlation','主值、周期延拓及相关目录的落点',[14,15,16,17,18,19],F(r'\widetilde x(n)=\sum_{r=-\infty}')+F(r'x(n)=\widetilde x(n)R_N(n)')+P('R<sub>N</sub>(n)在0…N−1内为1，其余为0。先把有限序列按N周期延拓，再移位，再截取主值，与直接模N索引相同。线性移位不绕回，窗口外的值仍存在。')+P('原P14还列“相关”，但并无相关推导页。相关比较信号与延迟版本的相似程度，通常涉及共轭；不把它与卷积的翻转规则混同。完整相关定义见本节末可选链接。'),level='deep'))
c.append(card('convolution-proof','折回关系与原书例2.3.10',[23,25,32,33,34],F(r'y_N(n)=\sum_{r=-\infty}^{\infty}y_l')+P('将圆周取值写成周期副本之和，交换有限的 m 求和与 r 求和，内层恰是线性卷积。频谱乘法的证明令 r=n−m，指数分成 W<sub>N</sub>ᵏᵐ·W<sub>N</sub>ᵏʳ；任取完整N点求和均相同。原P33显示的“m−n”与后续式不一致，这里统一为 n−m。')+P('<strong>原书例2.3.10</strong>（第3版印刷75–76页；课件旧引P68）：输入支持0…49与0…9；50点圆周卷积处处为12，线性卷积前5点为5，求尽可能多的线性输出。')+P('线性结果最多59点。由 y₅₀(n)=yₗ(n)+yₗ(n+50)，得到0…4为5，9…49为12，50…54为7；5…8与55…58各自不定，但每对相加为12。共确定51点，另8点不能凭现有条件拆开。'),level='deep'))
c.append(card('book-shifts','原书例2.3.7、2.3.8：把性质真正用一次',[31],P('<strong>例2.3.7</strong>（第3版印刷71页；课件旧引P64）：x=[4,3,2,1]作6点DFT，给 Y(k)=W₆⁴ᵏX(k)，求y。先补成[4,3,2,1,0,0]，负指数表示右移4，得到 <strong>[2,1,0,0,4,3]</strong>。')+P('<strong>例2.3.8</strong>：x(n)=δ(n)+2δ(n−5)，求10点DFT、乘频域移位因子后的y、以及时域调制后的DFT。')+UL(['原DFT：X(k)=1+2(−1)ᵏ，即[3,−1,3,−1,3,−1,3,−1,3,−1]。','Y(k)=exp(−j2π·3k/10)X(k)：右移3，y(n)=δ(n−3)+2δ(n−8)。','y(n)=exp(−j2π·3n/10)x(n)：只在0、5有值，分别为1、−2，所以Y(k)=1−2(−1)ᵏ=[−1,3,−1,3,−1,3,−1,3,−1,3]。'])+P('课件频移式与书中式(2.3.15)一致；不要把第2问的时移和第3问的调制混为一题。'),level='deep'))
c.append(card('symmetry-decomposition','两种拆分不能混成“实部对应实部”',list(range(40,54)),F(r'x_{ep}(n)=')+F(r'X_{ep}(k)=')+P('ep是圆周共轭对称，op是圆周共轭反对称；时间和频率各自定义，不能凭同名下标猜DFT对应。')+T(['时间侧','DFT频率侧'],[['Re x','X_ep'],['j Im x','X_op'],['x_ep','Re X'],['x_op','j Im X']])+P('证明只需对半和/半差用线性性，并用“取共轭↔共轭后频率反转”“共轭反转↔同频点共轭”两条性质。')+P('原六点数组[1,2,3,4,5,6]圆周反转为[1,6,5,4,3,2]，分解得ep=[1,4,4,4,4,4]、op=[0,−2,−1,0,1,2]。')+P('ep的实部偶、虚部奇；op的实部奇、虚部偶。两者模均偶；非零op配对点的相位之和为π（模2π），不是完全无关系。自配对点：ep值为实数，op值为纯虚数；后者不必为0。'),level='deep'))
c.append(card('two-real-sequences','原书例2.3.13：一次DFT分离两条实序列',[53],P('第3版印刷81–82页（课件旧引P73）。已知f=x+jy，x、y为N点实数组，且F为下式；求X、Y、x、y。按原解a、b为实数：')+F(r'F(k)=\frac{1-a^N}')+P('由实数组共轭对称，F*((−k) mod N)=X(k)−jY(k)。联立后：')+F(r'X(k)=\frac{F(k)+')+P('因此X=(1−aᴺ)/(1−aW<sub>N</sub>ᵏ)，Y=(1−bᴺ)/(1−bW<sub>N</sub>ᵏ)。各式展开为N项有限等比和，再作IDFT，得到 x(n)=aⁿ、y(n)=bⁿ（0≤n<N，区间外为0）。')+P('分母为0时回到有限和取N，不把有限数组误判成发散。原书演示a=0.8、b=0.6、N=32；不额外要求有限幂序列必须|a|<1。这里不能直接取Re F当X、Im F当Y，因为X、Y本身一般是复数。'),level='deep'))
ex={'title':'原课堂例：同一个输入，五种卷积结果','sourcePages':[24], 'problemHtml':P('原P24给 x=[1,2,2,1]，从n=0开始。求线性自卷积，以及N=4、6、7、8的圆周自卷积。'), 'stepsHtml':UL(['先按线性卷积逐项乘加：第0项1；第1项1×2+2×1=4；第2项1×2+2×2+2×1=8；第3项1+4+4+1=10，后面由对称性得8、4、1。','圆周结果把线性结果按下标 mod N分盒。N=4时，0号盒=1+8，1号盒=4+4，2号盒=8+1；N=6时只把末尾1加到首项。']), 'answerHtml':T(['运算','结果'],[['线性','[1,4,8,10,8,4,1]'],['N=4','[9,8,9,10]'],['N=6','[2,4,8,10,8,4]'],['N=7','[1,4,8,10,8,4,1]'],['N=8','[1,4,8,10,8,4,1,0]']]), 'checkHtml':P('各结果的样值和都为(1+2+2+1)²=36；N≥7时才完整保留线性结果。这同时检查乘加数值与补零长度。')}
D23={'id':'dsp-23','number':'2.3','title':'有限长序列的 DFT','brief':'先会选频点、识别圆周边界，再用性质少算几步。原53页合并重复证明，不丢页。','firstPassMinutes':25,'deepPassMinutes':35,'firstPass':['读8张必学卡，重点看大图与正逆变换的符号。','做原课堂卷积例；能判断补零长度与频谱共轭配对即可继续。','证明、完整对称分解与3组教材原题按需要展开；不要求第一遍读旧长正文。'],'source':{'title':'2.3有限长序列的离散傅里叶变换DFT.pptx','pageCount':53,'sha256':'80c4e87b080ddae66af7ed9ae83d35b058e60d7c0aef0765aa20cc32eaf881bc','editionNote':'课件旧引页与方勇第3版不同；原题按实际题干核对，书页另列。'},'cards':c,'example':ex,'pitfalls':['N、n、k各有角色；不能把频点编号k直接当数字角频率。','圆周卷积不是线性卷积；先看是否已补到L+M−1。','频域圆周卷积前的1/N、相位的正负号、共轭后的模N反转都不能漏。'],'deepLinks':[{'label':'原例完整系数与逐步证明（第二遍查阅）','href':'dsp-textbook/dsp-front-12.html'},{'label':'相关：原目录中提及的可选补充','href':'dsp-textbook/dsp-correlation.html'}]}
# 2.4 — five essential cards, three optional cards; no extra essay.
c=[]
c.append(card('sampling-question','只留 N 个频谱值，能恢复什么',[1,2,3],P('2.3从有限数组算DFT；这里反过来问：对任意长序列的DTFT只取N个等间隔点，再作IDFT，会得到原序列吗？先把输出另记为 x<sub>N</sub>，不能提前当成x。')+F(r'\omega_k=\frac{2\pi k}{N}')+F(r'x_N(n)=\frac1N')+P('普通函数情形可先假设x绝对可和；用Z变换说明时，要求单位圆属于收敛域。N个频谱值应是复数值，包含相位。'),pitfall='这是频域采样，不是再次对连续时间信号采样；它对应的混叠发生在时间上。'))
c.append(card('alias-identity','关键等式：相隔 N 的样值折到一起',[4],F(r'x_N(n)=\sum_{r=-\infty}^{\infty}x(n+rN),')+P('r遍历整数，表示前后所有周期副本。固定一个n，原序列n、n±N、n±2N…位置的值都会相加。IDFT只保留0…N−1这一段，段外若延拓则按N重复。'),figure=fig('24-residue-fold','五点矩形按四个余数盒折回','N=4时，原第4点进入第0盒；不是丢掉第4点。'),pitfall='原P4写“r为实数”是错误；这里必须为整数。'))
c.append(card('recover-condition','何时没有时域混叠',[5,6,7],P('若已知原序列只在0…M−1有值，且N≥M，主值区间内没有两个非零样值落入同一余数盒；于是x<sub>N</sub>(n)=x(n)，其余位置为0。')+P('N≥M保证这段内任意序列都不折叠。若N<M，一般只能得到折回后的和，不能唯一分开原样值；特殊零值或抵消不改变一般结论。若原支持区间不从0开始，须知道它的位置并重标索引；“非零点有M个”不等于任意分散的M点都不碰撞。')+P('无限长序列通常无法用有限N精确恢复；衰减尾部可使混叠误差变小，但不能不加条件地说“点越多必然无误差”。'),check=('两个脉冲分别在n=0、n=N，N点采样能区分它们吗？','不能：它们在全部采样频点的相位相同，IDFT只在第0盒看到两者之和。')))
c.append(card('rectangle-recovery','原图重绘：五点矩形，N 改变了什么',[6,8,9,10],P('原P8–P10用五个等高样值。按单位高度写成x=[1,1,1,1,1]。N=5时恰好不重叠；N=4时首尾两个1叠为2。书例2.4.1另用N=3和6，也放在同一图里比较。'),figure=fig('24-rectangle-fold','五点矩形按N=3、4、5、6折回的主值结果','所有小图的横轴都是主值时间位置 n；频率采样越密，时域副本间隔N越大。'),pitfall='原P9“周期个数等于N”应改为“周期长度等于N”；副本数仍是无限多个。'))
c.append(card('recover-spectrum','恢复整条频谱，先恢复有限数组',[2,7],P('知道序列确实只占0…N−1时，先由IDFT找回这N个样值，再代回DTFT，就能算任意ω处的频谱。这是精确重构，不是把频谱采样点用直线连起来。')+P('若原序列已经混叠，下面的内插只能恢复折回数组的频谱，不能自动分开原来相差N的样值。补零同样不会产生新的观测信息。'),check=('五点矩形补到8点再做DFT，能恢复原五点吗？','可以，IDFT恢复五个1和三个0；频谱更密，但原信息没有增加。')))
c.append(card('alias-proof','第二遍：为什么单位根只留下整数倍 N',[3,4],F(r'x_N(n)=\sum_{m=-\infty}^{\infty}x(m)')+P('括号中是N个单位根的平均。m−n是N的整数倍时每项为1；否则有限等比和为0。被留下的输入位置只能写成m=n+rN，其中r∈ℤ，于是得到折回等式。')+P('本推导可在绝对可和假设下交换有限频点求和与时间求和；周期序列的冲激DTFT不能不加说明地当作普通点值函数套用。'),level='deep'))
c.append(card('interpolation','第二遍：内插核与它的零分母',[2,7],P('时域支持在0…N−1时，把IDFT代入DTFT，得到：')+F(r'X(e^{j\omega})=\frac1N\sum_{k=0}^{N-1}X(k)D_N')+F(r'D_N(\theta)=')+P('分母为0时回到有限和：θ=2πr时D<sub>N</sub>=N。放回某个采样频率，只对应的核留下N，乘1/N恰好恢复该X(k)。若支持条件不满足，这个公式只重构折回数组的DTFT。'),level='deep'))
c.append(card('infinite-example','原书例2.4.2：指数尾巴仍会折回',[7,11],P('第3版印刷86–87页，课件旧引P79。原题x(n)=aⁿu(n)，0<a<1；在单位圆等距采N点，求x<sub>N</sub>=IDFT[X]。')+F(r'X(z)=\sum_{n=0}^{\infty}a^n')+F(r'X(k)=\frac1{1-aW_N^k}')+P('0≤n<N时，只有r≥0的副本有值，按等比和：')+F(r'x_N(n)=a^n+a^{n+N}')+P('主值区间相对误差为aᴺ/(1−aᴺ)。按原参数a=0.8：N=10约12.03%，N=40约0.0133%。原书N=10图延画了4个周期；IDFT本身仍只返回10点，不能把图上40点当成40点逆变换。'),level='deep',figure=fig('24-exponential-fold','无限长指数原值与N10、N40折回值的比较','曲线均按解析式计算；只比较共同的前10个主值点，不把周期延拓当作原指数继续衰减。')))
c.append(card('inverse-filter-reference','原P11的另一道题：逆滤波边界',[11],P('原P11同时列例2.6.3（旧引P95），不是第二个“指数尾巴题”。第3版原题在印刷102–103页，讨论H(z)=β/(1−αz⁻¹)，β≠0；N点DFT处理输出后再乘(1−αW<sub>N</sub>ᵏ)/β恢复输入。')+P('其IDFT实际是除以β的圆周差分：第1到N−1点使用窗口内前一点；第0点却使用第N−1点绕回，而不是线性系统窗口外的y(−1)。因此首项可能不等于原输入首项。完整原题与边界条件见下方可选原例链接，不把课件只列出的例号当作已给题干。'),level='deep'))
ex={'title':'用四个频率样本，手算五点矩形的恢复结果','sourcePages':[8,9,10],'problemHtml':P('x(n)在n=0…4均为1，其余为0。取DTFT在ω=0、π/2、π、3π/2的四个样本，再作4点IDFT。'),'stepsHtml':UL(['直接相加五个复指数：四个连续样值在非零频点相消，第五项每次都为1，因此X=[5,1,1,1]。','IDFT第0项：(5+1+1+1)/4=2。其余三项中，四个单位根相加为0，只留下额外的4/4=1。','从时域复核：n=0与4折进同一盒，另外三盒各有一个1。']),'answerHtml':P('<strong>x₄=[2,1,1,1]</strong>。这是原序列按4折回的主值，不是原五点数组。若改N=5，可得到[1,1,1,1,1]。'),'checkHtml':P('结果和仍为5，与频谱直流值X(0)=5一致；第0盒的2不能唯一拆成原来两个样值，说明N<M的恢复障碍。')}
D24={'id':'dsp-24','number':'2.4','title':'频域采样定理','brief':'频率只取有限点，时间就按 N 折回。先看折回发生在哪里，再判断能否恢复。','firstPassMinutes':20,'deepPassMinutes':20,'firstPass':['读5张必学卡，能解释“按余数分盒相加”。','做四频点恢复五样值的例题，核对N≥M还需要已知支持位置。','内插证明、无限指数原题及逆滤波首项留到第二遍。'],'source':{'title':'2.4频域采样定理.pptx','pageCount':11,'sha256':'53d6a04b132c0ed66d5feef880e99555033ac6eba57c999f32d94ec1c8377c5e','editionNote':'本稿核对第3版印刷85–87页；原例2.4.2实核86–87页。旧版P79/P95不可直接套用。'},'cards':c,'example':ex,'pitfalls':['频率采样导致时域周期叠加；不要写成时域采样导致的频谱混叠。','N是时域周期长度，不是周期副本个数；副本索引r必须是整数。','N≥M针对已知连续支持区间；只留幅度、支持位置未知或无限尾部时不能照搬结论。'],'deepLinks':[{'label':'原例2.4.2完整慢推导（可选）','href':'dsp-textbook/dsp-frequency-book-example.html'},{'label':'原例2.6.3：DFT逆滤波与首项边界（可选）','href':'dsp-textbook/dsp-inverse-filter.html'}]}
# Build exhaustive, auditable page maps and record mathematical source metadata.
for num,d in [('23',D23),('24',D24)]:
    d['pageMap']=[{'page':p,'cardIds':[c['id'] for c in d['cards'] if p in c['sourcePages']],'note':'重复原页合并到同一知识卡；证明保留在折叠的第二遍。'} for p in range(1,d['source']['pageCount']+1)]
    assert all(r['cardIds'] for r in d['pageMap'])
    d['source']['textbook']={'title':'方勇《数字信号处理——原理与实践》第3版（2021）','printedPages':[63,84] if num=='23' else [85,87],'pdfPageOffset':17,'note':'核对材料不公开；课件旧引页另列。'}
    d['textbook']={'printedPages':list(range(63,85)) if num=='23' else [85,86,87], 'pdfPages':list(range(80,102)) if num=='23' else [102,103,104]}
    d['sourceNote']='课件引用旧版教材页码；本稿按方勇第3版实际题干核对，旧引页与现书页分列。原书扫描仅作私有核对，不公开。'
    (OUT/f'ch2-{num}.json').write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
    visible=''.join(c['bodyHtml'] for c in d['cards'] if c['level']=='essential')+''.join(v for k,v in d['example'].items() if k.endswith('Html'))
    for el in html.fromstring('<div>'+visible+'</div>').xpath('//math'):
        el.getparent().remove(el)
    chars=len(re.findall(r'[\u4e00-\u9fff]',html.fromstring('<div>'+visible+'</div>').text_content()))
    print(num,len(d['cards']),'cards;',sum(c['level']=='essential' for c in d['cards']),'essential;',chars,'Chinese characters including example (not formula symbols)')
print('Built',len(list(AS.glob('23-*.svg')))+len(list(AS.glob('24-*.svg'))),'scientific SVGs')
