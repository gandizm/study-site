from pathlib import Path
import math, html

OUT=Path(__file__).resolve().parents[1]/'site/communications-redraw/assets'
OUT.mkdir(parents=True,exist_ok=True)
GREEN='#17745b'; INK='#17372f'; GOLD='#bd761b'; BLUE='#416dab'; RED='#b74642'; MUTED='#60736b'

class SVG:
    def __init__(self,h,title,desc):
        self.h=h; self.s=[f'<svg xmlns="http://www.w3.org/2000/svg" width="1100" height="{h}" viewBox="0 0 1100 {h}" role="img" aria-labelledby="title desc"><title id="title">{html.escape(title)}</title><desc id="desc">{html.escape(desc)}</desc><rect width="1100" height="{h}" fill="#fffefa"/><g font-family="system-ui, Noto Sans CJK SC, sans-serif" fill="{INK}">']
    def txt(self,x,y,t,size=22,color=INK,anchor='start',weight='normal'):
        self.s.append(f'<text x="{x}" y="{y}" font-size="{size}" fill="{color}" text-anchor="{anchor}" font-weight="{weight}">{html.escape(t)}</text>')
    def line(self,x1,y1,x2,y2,color=MUTED,w=2,dash=''):
        self.s.append(f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{color}" stroke-width="{w}"'+(f' stroke-dasharray="{dash}"' if dash else '')+'/>')
    def path(self,pts,color=GREEN,w=3,fill='none',dash=''):
        self.s.append('<polyline points="'+' '.join(f'{x:.2f},{y:.2f}' for x,y in pts)+f'" fill="{fill}" stroke="{color}" stroke-width="{w}"'+(f' stroke-dasharray="{dash}"' if dash else '')+'/>')
    def circle(self,x,y,r=6,color=GOLD):self.s.append(f'<circle cx="{x}" cy="{y}" r="{r}" fill="{color}"/>')
    def rect(self,x,y,w,h,color,opacity=1):self.s.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="{color}" opacity="{opacity}"/>')
    def save(self,name): (OUT/name).write_text(''.join(self.s)+ '</g></svg>')

s=SVG(850,'同一条信号：连续曲线、抽样点、量化档位','横轴是毫秒时间，纵轴是电压。每1毫秒测一次，得到0.07、0.31、0.62和0.88伏；量化到0.2伏间隔档位后得到0、0.4、0.6和0.8伏。')
s.txt(45,48,'先读一个点，再区分两种“离散”',30,weight='bold')
s.txt(45,88,'自编示意：这里的量化档位是0、0.2、0.4……V，不是A律表。',21,color=MUTED)
vals=[.07,.31,.62,.88]
def value(t): return .07+.165*t+.095*t*t-.02*t*t*t
for row,(title,kind) in enumerate([('① 原曲线：每个时刻都有值','curve'),('② 抽样：只取时刻，幅度还可连续','sample'),('③ 量化：样值改成有限档位','quant')]):
    top=125+row*225;base=top+145;x0=195;scale=235;sy=120
    s.txt(45,top,title,23,weight='bold');s.txt(48,top+54,'电压 / V',19)
    s.line(x0,top+20,x0,base);s.line(x0,base,1000,base)
    s.txt(1007,base+6,'t',21)
    for y in [0,.5,1]:
        py=base-y*sy;s.line(x0-5,py,x0+780,py,color='#e1e8de',w=1);s.txt(x0-12,py+7,str(y),18,anchor='end')
    for i,v in enumerate(vals):
        x=x0+i*scale;s.line(x,base,x,base-125,color='#d6dfd7',w=1,dash='5 4');s.txt(x,base+28,str(i),19,anchor='middle')
        if kind!='curve':
            q=round(v/.2)*.2 if kind=='quant' else v
            s.line(x,base,x,base-q*sy,color=GREEN,w=3);s.circle(x,base-q*sy);s.txt(x+11,base-q*sy-10,f'{q:.2f} V',19)
    s.txt(1000,base+55,'时间 / ms',19,anchor='end')
    if kind in ['curve','sample']:s.path([(x0+t*scale,base-value(t)*sy) for t in [i/100 for i in range(331)]],GREEN,3,dash='' if kind=='curve' else '6 4')
s.txt(45,817,'抓住两件事：抽样决定“什么时候测”；量化决定“测出的数记多精细”。',23,color=GREEN,weight='bold')
s.save('novice-signal-samples.svg')

s=SVG(1120,'逐步读三角频谱、平移副本和混叠','先画从负200至200赫兹的三角频谱。以400赫兹为间隔复制时端点相接；以300赫兹复制时100至200赫兹重叠，150赫兹处两个0.25相加为0.5。示意先除以抽样率显示归一化高度。')
s.txt(42,48,'原谱 → 只移一份 → 找交叠 → 加高度',29,weight='bold')
s.txt(42,87,'横轴f是频率，不是时间。前面先画形状；真实理想抽样谱还要乘fs。',21,color=MUTED)
x=lambda f:160+(f+250)*.96
for row,(title,shift) in enumerate([('① 原谱：中心0，底边−200～200 Hz',None),('② fs=400 Hz：右副本移到400，底边200～600',400),('③ fs=300 Hz：右副本移到300，底边100～500',300)]):
    top=135+row*272;base=top+158
    s.txt(42,top,title,23,weight='bold');s.txt(45,top+45,'归一化高度',18)
    s.line(130,base,1040,base);s.line(x(0),base+9,x(0),base-132,color=MUTED)
    s.path([(x(-200),base),(x(0),base-120),(x(200),base)],GREEN,4)
    s.txt(x(0)-12,base-125,'1',20,color=GREEN,anchor='end')
    ticks=[-200,0,200] if shift is None else ([-200,0,200,400,600] if shift==400 else [-200,0,100,200,300,500])
    for f in ticks:s.line(x(f),base,x(f),base+7);s.txt(x(f),base+30,str(f),19,anchor='middle')
    s.txt(1010,base+60,'f / Hz',19,anchor='end')
    if shift:
        s.path([(x(shift-200),base),(x(shift),base-120),(x(shift+200),base)],BLUE,4,dash='9 6')
        s.txt(x(shift),base-135,'只复制右边这一份',19,color=BLUE,anchor='middle')
        if shift==300:
            s.rect(x(100),base-120,x(200)-x(100),120,GOLD,.14)
            s.line(x(150),base,x(150),base-60,GOLD,3)
            s.circle(x(150),base-30,5,GOLD)
            s.line(x(100),base-60,x(200),base-60,RED,5)
            s.txt(42,base+108,'150 Hz：0.25 + 0.25 = 0.50',21,color=RED)
            s.txt(470,base+108,'红色线段 = 重叠后的高度和',19,color=RED)
    s.txt(44,base+64, '先看每个点对应哪个频率。' if shift is None else ('只在200 Hz的零值端点接触。' if shift==400 else '100～200 Hz的重叠段必须逐点相加。'),21,color=GREEN)
s.txt(42,1010,'本图省略更远的副本，只教“先移一份”。完整周期谱见作业5.9.1。',21,color=MUTED)
s.txt(42,1060,'fs=300 Hz时：150 Hz处实际高度 = 300 × 0.50 = 150。',24,color=GREEN,weight='bold')
s.save('novice-spectrum-steps.svg')

s=SVG(1100,'理想抽样、自然抽样与平顶抽样对照','同一个输入在每个抽样时刻被取样。理想抽样用冲激权重示意；自然抽样在开门期间保持跟随输入；平顶抽样在开门起点抓取样值并保持。脉宽tau与抽样周期Ts不同。')
s.txt(42,49,'一次“开窗”与一次“拍照”不是同一个动作',28,weight='bold')
s.txt(42,90,'同一输入、同一组抽样时刻；仅改变输出如何保持。图仅演示，不是量化。',21,color=MUTED)
X=lambda t:170+t*230
Y=lambda t:.50+.34*math.sin(2*math.pi*t/3.7-.6)
for row,title in enumerate(['① 连续输入：随时间改变','② 理想抽样：箭头权重表示样值','③ 自然抽样：开窗期间跟随曲线','④ 平顶抽样：抓住起点读数后保持']):
    top=140+row*215;base=top+135
    s.txt(42,top,title,23,weight='bold');s.txt(45,top+55,'权重示意' if row==1 else '电压',18)
    s.line(145,base,1040,base);s.line(X(0),base,X(0),base-120)
    for k in range(4):
        s.line(X(k),base+2,X(k),base-114,color='#cad7ce',w=1,dash='5 4');s.txt(X(k),base+28,str(k),19,anchor='middle')
    if row==0:s.path([(X(t),base-Y(t)*120) for t in [i/100 for i in range(371)]],GREEN,4)
    else:
        s.path([(X(t),base-Y(t)*120) for t in [i/100 for i in range(371)]],'#aabdb3',2,dash='6 5')
        for k in range(4):
            if row==1:
                y=base-Y(k)*120;s.line(X(k),base,X(k),y,GREEN,3);s.path([(X(k)-6,y+10),(X(k),y),(X(k)+6,y+10)],GREEN,3)
            else:
                tau=.28;y0=base-Y(k)*120
                pts=[(X(k),base),(X(k),y0)]
                pts+=([(X(k+i*tau/35),base-Y(k+i*tau/35)*120) for i in range(36)] if row==2 else [(X(k+tau),y0)])
                pts.append((X(k+tau),base));s.path(pts,GREEN,4)
    s.txt(918,base+55,'时间 / ms',19)
    if row==3:
        s.line(X(0),base+55,X(1),base+55,GOLD,2);s.txt((X(0)+X(1))/2,base+80,'Ts：两次起点的间隔',19,color=GOLD,anchor='middle')
        s.line(X(2),base+55,X(2.28),base+55,BLUE,4);s.txt(X(2.14),base+80,'τ：保持时长',19,color=BLUE,anchor='middle')
s.txt(42,1070,'注意：保持0.314159 V仍允许任意幅度；只有量化才把它归到有限档位。',22,color=GREEN)
s.save('novice-sampling-types.svg')
print('wrote 3 foundation SVGs')
