#!/usr/bin/env python3
"""Original vector teaching figures. No textbook scans or personal data."""
from pathlib import Path
import math
from html import escape

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'site/communications-redraw/assets'
OUT.mkdir(parents=True, exist_ok=True)
INK, GREEN, ORANGE, BLUE, MUTED = '#183a32', '#22765d', '#b57524', '#4666a5', '#61756d'

def begin(title, desc, height=460):
    return [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1000 {height}" role="img" aria-labelledby="title desc"><title id="title">{escape(title)}</title><desc id="desc">{escape(desc)}</desc><rect width="1000" height="{height}" fill="#fffefa"/><style>text{{font-family:system-ui,"Noto Sans CJK SC","Microsoft YaHei",sans-serif;fill:{INK}}}.title{{font-size:27px;font-weight:750}}.label{{font-size:19px}}.small{{font-size:16px;fill:{MUTED}}}.axis{{stroke:#90a299;stroke-width:1.5}}.grid{{stroke:#dce5dd;stroke-width:1;stroke-dasharray:5 5}}</style>', f'<text class="title" x="35" y="44">{escape(title)}</text>']

def text(s, x, y, value, cls='label', color=None, anchor=None):
    s.append(f'<text class="{cls}" x="{x}" y="{y}"'+(f' style="fill:{color}"' if color else '')+(f' text-anchor="{anchor}"' if anchor else '')+f'>{escape(str(value))}</text>')

def line(s,x1,y1,x2,y2,color='#90a299',width=1.5,dash=None):
    s.append(f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{color}" stroke-width="{width}"'+(f' stroke-dasharray="{dash}"' if dash else '')+'/>')

def poly(s, pts, color=GREEN, width=3):
    s.append('<polyline fill="none" stroke="'+color+'" stroke-width="'+str(width)+'" points="'+' '.join(f'{x:.2f},{y:.2f}' for x,y in pts)+'"/>')

def save(name,s):
    (OUT/name).write_text('\n'.join(s+['</svg>']),encoding='utf-8')

s=begin('三章只做三件事：取数 → 传数 → 搬上载波','第5章将连续消息变成比特；第6章把比特变成可判决的基带波形；第7章将数字波形调制到载波传输。',420)
for x,n,title,detail,c in [(35,'05','模拟 → 数字','抽样 · 量化 · 编码',GREEN),(360,'06','比特 → 基带波形','码型 · 成形 · 判决',BLUE),(685,'07','基带 → 载波','ASK · FSK · PSK',ORANGE)]:
    s.append(f'<rect x="{x}" y="95" width="280" height="185" rx="18" fill="#f1f5ed" stroke="#d6e1d7"/>')
    text(s,x+22,132,n,'title',c);text(s,x+22,185,title);text(s,x+22,230,detail,'small')
for x in [320,645]: text(s,x,192,'→','title')
text(s,35,330,'同一条消息：话音波形 → 一串 0/1 → 可在线路上传输的电压 → 适合信道的带通信号')
text(s,35,376,'反向接收：解调 → 抽样判决 → PCM译码 → 重建模拟波形','small')
save('three-chapter-chain.svg',s)

def triangle(f): return max(0,1-abs(f)/200)
s=begin('抽样频谱：副本相加，混叠看有没有重叠','原频谱为最高200 Hz的三角形。上图300 Hz抽样时副本重叠，下图400 Hz抽样时边缘恰好相接。纵轴为Ms除以fs。',620)
for row,fs in enumerate([300,400]):
    oy=245+row*260; x0=500; sx=.55; sy=120
    text(s,35,94+row*260,f'fₛ = {fs} Hz：'+('有混叠' if fs==300 else '理想临界，边缘为零'),color=ORANGE if fs==300 else GREEN)
    line(s,70,oy,935,oy);text(s,930,oy+32,'f / Hz','small')
    for f in [-600,-400,-200,0,200,400,600]:
        x=x0+sx*f;line(s,x,oy,x,oy-145,'#dce5dd',1,'4 4');text(s,x,oy+24,f,'small',anchor='middle')
    for k in range(-3,4):
        pts=[(x0+sx*f,oy-sy*triangle(f-k*fs)) for f in range(-780,781,2)]
        poly(s,pts,BLUE if k%2 else ORANGE,1.6)
    pts=[(x0+sx*f,oy-sy*sum(triangle(f-k*fs) for k in range(-4,5))) for f in range(-780,781,2)]
    poly(s,pts,GREEN,3.5)
    text(s,55,oy-123,'1','small');text(s,740,oy-162,'Mₛ(f) / fₛ','small')
text(s,35,594,'细线：移位副本。粗绿线：实际相加结果。采用单位面积冲激列时，未归一化峰值还要乘 fₛ。','small')
save('sampling-replicas.svg',s)

s=begin('均匀量化：样值落在区间内，输出取重建电平','0到20伏分成40个区间，每区间0.5伏。中点重建的最低输出0.25伏，最高输出19.75伏。',360)
text(s,35,90,'本图：范围 0～20 V，40个区间，Δ = 0.5 V；采用中点重建')
line(s,85,205,915,205)
for x,v in [(90,'0'),(240,'0.5'),(390,'1.0'),(610,'19.0'),(760,'19.5'),(910,'20.0')]:
    line(s,x,180,x,230);text(s,x,260,v+' V','small',anchor='middle')
for x,v in [(165,'0.25'),(315,'0.75'),(685,'19.25'),(835,'19.75')]:
    s.append(f'<circle cx="{x}" cy="205" r="7" fill="{GREEN}"/>');text(s,x,158,v+' V','small',GREEN,'middle')
text(s,485,213,'…','title');text(s,35,318,'边界 ≠ 输出电平。输入到20 V，并不意味着重建值也等于20 V。','small')
save('quantization-midpoint.svg',s)

s=begin('同一串 1 0 1 1：比特不变，线路码型可以变','单极NRZ将1映射到正电平、0到0；双极NRZ将1映射到正电平、0到负电平；AMI的1交替极性，0为0。',550)
bits=[1,0,1,1]
for i,b in enumerate(bits):text(s,280+i*155,95,str(b),'title',anchor='middle')
for row,(label,values,color) in enumerate([('单极 NRZ',[1,0,1,1],GREEN),('双极 NRZ',[1,-1,1,1],BLUE),('AMI',[1,0,-1,1],ORANGE)]):
    oy=190+row*145; text(s,30,oy,label);line(s,200,oy,850,oy)
    for i in range(5):line(s,202+i*155,oy-54,202+i*155,oy+54,'#dce5dd',1,'4 4')
    pts=[]
    for i,v in enumerate(values):pts.extend([(202+i*155,oy-v*40),(202+(i+1)*155,oy-v*40)])
    poly(s,pts,color,4);text(s,875,oy,'0','small');text(s,875,oy-36,'+A','small');text(s,875,oy+40,'−A','small')
save('line-codes.svg',s)

s=begin('波形可以重叠，判决时刻仍互不干扰','两个sinc脉冲在时间上重叠，但分别在其他码元的整数抽样点为零。无ISI并不是整个时域互不重叠。',420)
x0=495;sx=105;oy=285;sy=130
line(s,60,oy,940,oy)
def sinc(x):return 1 if abs(x)<1e-10 else math.sin(math.pi*x)/(math.pi*x)
for k in range(-4,5):
    x=x0+sx*k;line(s,x,95,x,310,'#dce5dd',1,'4 4');text(s,x,335,str(k),'small',anchor='middle')
for shift,col in [(0,GREEN),(1,BLUE)]:
    poly(s,[(x0+sx*x,oy-sy*sinc(x-shift)) for x in [i/100 for i in range(-400,401)]],col,3)
    for k in range(-3,4):s.append(f'<circle cx="{x0+sx*k}" cy="{oy-sy*sinc(k-shift)}" r="4" fill="{col}"/>')
text(s,40,88,'绿：p(t) = sinc(t/Tₛ)     蓝：p(t−Tₛ) = sinc(t/Tₛ−1)','small')
text(s,730,375,'横轴 t/Tₛ','small');text(s,35,392,'在 t = 0：绿为1，蓝为0；在 t = Tₛ：绿为0，蓝为1。这里画的是单个脉冲，不是总接收波形。','small')
save('zero-isi-sinc.svg',s)

s=begin('升余弦：用额外带宽换更快衰减的时域尾巴','固定符号率Rs时，升余弦滚降系数alpha越大，低通信道带宽越大，为(1+alpha)Rs/2；理想脉冲均在非零整数倍Ts处为零。',620)
for a,col in [(0,GREEN),(.5,BLUE),(1,ORANGE)]:
    pts=[]
    for i in range(501):
        f=i/400
        if f<=(1-a)/2:v=1
        elif a>0 and f<(1+a)/2:v=.5*(1+math.cos(math.pi/a*(f-(1-a)/2)))
        else:v=0
        pts.append((90+680*f,270-120*v))
    poly(s,pts,col,3)
line(s,90,270,940,270);text(s,35,92,'频域（正频率部分）：H(f)/Tₛ','label')
for f in [0,.25,.5,.75,1]:text(s,90+680*f,300,str(f),'small',anchor='middle')
text(s,855,330,'f/Rₛ','small')
for a,col in [(0,GREEN),(.5,BLUE),(1,ORANGE)]:
    pts=[]
    for i in range(-500,501):
        t=i/100
        if a and abs(abs(2*a*t)-1)<1e-8:v=math.pi/4*sinc(1/(2*a))
        else:v=sinc(t)*math.cos(math.pi*a*t)/(1-(2*a*t)**2)
        pts.append((510+t*84,525-v*120))
    poly(s,pts,col,2.5)
line(s,80,525,940,525);text(s,35,363,'时域：p(t)，所有曲线的整数抽样点保持零ISI','label')
for t in range(-5,6):text(s,510+t*84,553,str(t),'small',anchor='middle')
text(s,850,583,'t/Tₛ','small')
text(s,530,92,'α=0','small',GREEN);text(s,650,92,'α=0.5','small',BLUE);text(s,790,92,'α=1','small',ORANGE)
save('raised-cosine.svg',s)

s=begin('双极判决：噪声把两种发送值散成两团','等概双极符号正负A叠加同方差高斯噪声，最优门限为零。发送正A却落到零左边，以及发送负A却落到零右边，构成错误。',420)
x0=500;sx=135;oy=295;sy=440
line(s,65,oy,935,oy);line(s,x0,110,x0,315,ORANGE,2,'5 4')
for mu,col in [(-1.5,BLUE),(1.5,GREEN)]:
    pts=[(x0+sx*x,oy-sy*math.exp(-(x-mu)**2/2)/math.sqrt(2*math.pi)) for x in [i/100 for i in range(-320,321)]]
    poly(s,pts,col,3)
    text(s,x0+sx*mu,336,'−A' if mu<0 else '+A','label',col,'middle')
text(s,505,100,'门限 0','small',ORANGE);text(s,120,375,'左半区 → 判负电平 / 0','small',BLUE);text(s,600,375,'右半区 → 判正电平 / 1','small',GREEN)
text(s,35,82,'条件：等概先验、相同高斯噪声方差、对称双极映射。不是所有接收机门限都等于0。','small')
save('binary-decision.svg',s)

s=begin('同一比特串，分别改变幅度、频率、相位','示例比特为1011。ASK的1有载波，0无载波；FSK的1用较高频率，0用较低频率；PSK的0为零相位、1为π相位。',610)
bits=[1,0,1,1]
for i,b in enumerate(bits):text(s,260+i*165,94,str(b),'title',anchor='middle')
for row,(label,col) in enumerate([('2ASK',GREEN),('2FSK',BLUE),('2PSK',ORANGE)]):
    oy=190+row*155;text(s,35,oy,label);line(s,170,oy,880,oy)
    for k in range(5):line(s,177+k*165,oy-55,177+k*165,oy+55,'#dce5dd',1,'4 4')
    for k,b in enumerate(bits):
        pts=[]
        for j in range(166):
            u=j/165
            v=(b*math.cos(6*math.pi*u) if row==0 else math.cos((8 if b else 4)*math.pi*u) if row==1 else (-1 if b else 1)*math.cos(6*math.pi*u))
            pts.append((177+k*165+j,oy-38*v))
        poly(s,pts,col,2.5)
text(s,35,582,'这是画图约定：2PSK 的“0→0相位、1→π相位”。改变标签不改变抗噪结论，但收发必须一致。','small')
save('digital-modulations.svg',s)

s=begin('QPSK：一个码元用两个正交方向承载两个比特','四个相位相差90度的等能量点构成QPSK星座，每码元承载两比特。本图的标签约定与本章正文一致。',520)
cx,cy,r=500,285,160
line(s,225,cy,775,cy);line(s,cx,465,cx,85)
s.append(f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="none" stroke="#d4dfd5" stroke-dasharray="5 5"/>')
for deg in [45,135,225,315]:
    th=math.radians(deg);x=cx+r*math.cos(th);y=cy-r*math.sin(th);line(s,cx,cy,x,y,'#9bb5a4',2)
    s.append(f'<circle cx="{x}" cy="{y}" r="9" fill="{GREEN}"/>');text(s,x+(20 if x>cx else -20),y-18,f'{deg}° / '+{45:'00',135:'10',225:'11',315:'01'}[deg],'label',anchor='start' if x>cx else 'end')
text(s,795,293,'I');text(s,490,77,'Q');text(s,35,90,'示意：四点等能量，符号率 Rₛ = R_b / 2','small')
text(s,35,490,'本章约定：I=1−2u，Q=1−2v。相邻点仅一位不同；每码元2 bit，Eₛ=2E_b。','small')
save('qpsk-constellation.svg',s)

s=begin('5.9.3：先滤波，再抽样，恢复时还要把衰减补回来','输入矩形谱在正负ω1内为1；H1是正负2ω1之间的三角形；滤波后频谱仍只到正负ω1，但边缘幅度降到1/2。',450)
for index,label in enumerate(['M(ω)','H₁(ω)','M′(ω)=M(ω)H₁(ω)']):
    cx=185+index*320;oy=285;text(s,cx,115,label,'label',anchor='middle');line(s,cx-130,oy,cx+130,oy);line(s,cx,oy-135,cx,oy+20)
    if index==0:pts=[(cx-120,oy),(cx-60,oy),(cx-60,oy-110),(cx+60,oy-110),(cx+60,oy),(cx+120,oy)]
    elif index==1:pts=[(cx-120,oy),(cx,oy-110),(cx+120,oy)]
    else:pts=[(cx-120,oy),(cx-60,oy),(cx-60,oy-55),(cx,oy-110),(cx+60,oy-55),(cx+60,oy),(cx+120,oy)]
    poly(s,pts,[GREEN,BLUE,ORANGE][index],3)
    for offset,lab in [(-60,'−ω₁'),(60,'ω₁')]:text(s,cx+offset,oy+30,lab,'small',anchor='middle')
    if index==1:
        text(s,cx-120,oy+58,'−2ω₁','small',anchor='middle');text(s,cx+120,oy+58,'2ω₁','small',anchor='middle')
text(s,35,390,'没有产生新频率：m′(t) 的最高频率仍为 f₁，所以理想最低抽样率仍按 2f₁ 判断。','small')
text(s,35,423,'但恢复原始 m(t) 时，通带中 H₂(ω) 需要同时补偿抽样尺度与 H₁(ω) 的衰减。','small')
save('homework-filter-spectrum.svg',s)

s=begin('A律第4段：先找小格，再用中点代表整格','幅度95落在第4段的第8个小格，区间92至96，中点94。负输入恢复负号后为负94，折叠段内码只改变标签，不改变量化区间。',360)
text(s,35,92,'输入 −95：先处理幅度95。第4段起点64，步长4，编号 j = 7。')
line(s,100,210,900,210)
for x,val in [(150,'88'),(370,'92'),(590,'96'),(810,'100')]:
    line(s,x,185,x,240);text(s,x,270,val,'label',anchor='middle')
s.append('<rect x="370" y="185" width="220" height="55" rx="5" fill="#d9e9d6" opacity=".8"/>')
s.append(f'<circle cx="480" cy="210" r="8" fill="{GREEN}"/><circle cx="535" cy="210" r="7" fill="{ORANGE}"/>')
text(s,455,150,'重建幅度94','small',GREEN,'end');line(s,470,155,480,194,GREEN)
text(s,555,150,'输入幅度95','small',ORANGE);line(s,545,155,535,194,ORANGE)
text(s,35,325,'自然编号7 → 自然段内码0111 → 本题折叠码0000；恢复负号后输出−94。','small')
save('alaw-cell.svg',s)

s=begin('24路PAM：一帧容纳24个时隙，每个脉冲占半个时隙','每路按8000次每秒抽样，一帧125微秒，24路复用码元率192千波特，每时隙5.208微秒，矩形脉冲宽度2.604微秒。',450)
text(s,35,92,'每路 fₛ = 8 kHz → 每帧125 μs → 24路合成 Rₛ = 192 kBaud')
for i in range(24):
    x=60+i*36;s.append(f'<rect x="{x}" y="145" width="36" height="50" fill="'+('#e3eddc' if i%2==0 else '#eff3e8')+'" stroke="#a2b5a6"/>')
    if i<3 or i>20:text(s,x+18,176,str(i+1),'small',anchor='middle')
text(s,488,176,'…','small',anchor='middle');text(s,60,225,'一帧：每路轮到一次','small')
line(s,220,350,820,350)
s.append(f'<polyline points="250,350 250,275 475,275 475,350 700,350" fill="none" stroke="{GREEN}" stroke-width="4"/>')
line(s,250,258,250,378,'#a2b5a6',1,'4 4');line(s,700,258,700,378,'#a2b5a6',1,'4 4')
text(s,280,257,'脉宽 τ = 2.604 μs','small',GREEN);text(s,310,410,'一个时隙 T = 5.208 μs；占空比 τ/T = 0.5','small')
save('tdm-slots.svg',s)
print(f'Wrote {len(list(OUT.glob("*.svg")))} SVG figures to {OUT}')
