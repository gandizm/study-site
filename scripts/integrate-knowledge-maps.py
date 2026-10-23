#!/usr/bin/env python3
"""Integrate reviewed maps without rewriting the source slides or lesson articles."""
import hashlib
from html import escape
import json
from pathlib import Path
import re
ROOT=Path(__file__).resolve().parents[1]
SITE=ROOT/'site'
LESSONS=[('communications-ch4', 'communications-ppt.html', '通信原理 · 第4章模拟调制系统', 105), ('network-ch2', 'network-ch2-ppt.html', '计算机网络 · 第二章物理层', 50), ('communications-ch1', 'communications-ch1-ppt.html', '通信原理 · 第1章绪论', 94), ('network-wireless', 'network-wireless-ppt.html', '计算机网络 无线网络基础', 75), ('network-wireless-app', 'network-wireless-app-ppt.html', '计算机网络 无线局域网工程应用', 55), ('network-intro', 'network-intro-ppt.html', '计算机网络 课程导学', 11), ('network-ch2-interfaces', 'network-ch2-interfaces-ppt.html', '计算机网络 物理接口专题', 8), ('em-ch0', 'ppt0.html', '电磁场绪论 · 建模、理论骨架与读图', 20), ('em-ch1', 'ppt1.html', '电磁场第1章 · 矢量分析', 42), ('communications-ch2', 'communications-ch2-ppt.html', '通信原理 第2章：确知信号与频谱', 64), ('dsp-21', 'dsp-21-ppt.html', '数字信号处理 2.1：离散时间傅里叶变换', 35), ('dsp-22', 'dsp-22-ppt.html', '数字信号处理 2.2：周期序列与采样频谱', 24), ('em-ch2', 'ppt2.html', '电磁场第2章 · 场方程、边界与能量', 57), ('em-ch3', 'ppt3.html', '电磁场第3章 · 静电边值、镜像与分离变量', 24), ('em-ch5', 'ppt5.html', '电磁场第5章 · 相量、平面波、损耗与极化', 78), ('em-ch6', 'ppt6.html', '电磁场第6章 · 反射、折射、导波与全反射', 74), ('em-ch7', 'ppt7.html', '电磁场第7章 · 位函数、电流元与小环辐射', 35), ('network-ch1-foundations', 'network-ch1-foundations-ppt.html', '计算机网络 第一章：基础与体系结构', 103), ('network-ch3', 'network-ch3-ppt.html', '计算机网络 第三章 数据链路层', 149)]
def version(path):return hashlib.sha256((SITE/path).read_bytes()).hexdigest()[:12]
def main():
 rows=[]
 for chapter,reader,title,count in LESSONS:
  data_path=f'courses/{chapter}/knowledge-map.json';data=json.loads((SITE/data_path).read_text(encoding='utf-8'))
  text=(SITE/reader).read_text(encoding='utf-8')
  text=re.sub(r'<script\b[^>]*\bdata-knowledge-map="[^"]*"[^>]*>\s*</script>','',text)
  text=re.sub(r'<script\b[^>]*\bsrc="[^"]*knowledge-neighborhood\.js[^"]*"[^>]*>\s*</script>','',text)
  for css in ['knowledge-map.css','knowledge-reader-shell.css','knowledge-neighborhood.css']:
   text=re.sub(r'<link\b[^>]*\bhref="[^"]*'+re.escape(css)+r'[^"]*"[^>]*>','',text)
   text=text.replace('</head>',f'<link rel="stylesheet" href="/study-site/{css}?v={version(css)}"></head>',1)
  tags=f'<script src="/study-site/knowledge-map.js?v={version("knowledge-map.js")}" defer data-knowledge-map="/study-site/{data_path}?v={version(data_path)}"></script>'
  tags+=f'<script src="/study-site/knowledge-neighborhood.js?v={version("knowledge-neighborhood.js")}" defer></script>'
  text=text.replace('</body>',tags+'</body>',1);(SITE/reader).write_text(text,encoding='utf-8')
  rows.append({'chapterId':chapter,'title':title,'readerPath':reader,'knowledgeMapPath':data_path,'readerPageCount':count,'nodeCount':len(data['nodes']),'startPage':min(p for n in data['nodes'] for p in n['pages'])})
 (SITE/'knowledge-map-registry.json').write_text(json.dumps({'schemaVersion':1,'maps':rows},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
 cards=''.join(f'<section class="card"><h2>{escape(x["title"])}</h2><p>{x["readerPageCount"]}个真实课件页 · {x["nodeCount"]}个概念节点</p><a class="primary" href="/study-site/{x["readerPath"]}?map=1#p{x["startPage"]:02d}">打开常驻知识图谱</a></section>' for x in rows)
 (SITE/'knowledge-maps.html').write_text('<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>知识图谱 · 课程伴学</title><link rel="stylesheet" href="/study-site/course-hub.css"></head><body><main><nav class="course-nav"><a href="/study-site/courses.html">学习首页</a><a href="/study-site/communications.html">通原目录</a><a href="/study-site/network.html">计网目录</a></nav><header><h1>从概念连线回到真实课件页</h1><p>节点连线展示先修、对比与应用关系；切到概念清单可搜索。点击页码后图谱仍然保留，讲义与原图同步跳转。</p></header>'+cards+'<aside class="note">这里只列本批已接入的图谱，不把预览镜像重复计数。翻页不会自动标记已读；你的原学习进度保持独立。</aside></main></body></html>',encoding='utf-8')
 print(f'Integrated {len(rows)} maps')
if __name__=='__main__':main()
