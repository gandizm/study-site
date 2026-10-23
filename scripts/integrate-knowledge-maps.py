#!/usr/bin/env python3
"""Integrate reviewed maps without rewriting the source slides or lesson articles."""
import hashlib
from html import escape
import json
from pathlib import Path
import re
ROOT=Path(__file__).resolve().parents[1]
SITE=ROOT/'site'
LESSONS=[('communications-ch4','communications-ppt.html','通信原理 · 第4章模拟调制系统',105),('network-ch2','network-ch2-ppt.html','计算机网络 · 第二章物理层',50),('communications-ch1','communications-ch1-ppt.html','通信原理 · 第1章绪论',94)]
def version(path):return hashlib.sha256((SITE/path).read_bytes()).hexdigest()[:12]
def main():
 rows=[]
 for chapter,reader,title,count in LESSONS:
  data_path=f'courses/{chapter}/knowledge-map.json';data=json.loads((SITE/data_path).read_text())
  text=(SITE/reader).read_text()
  text=re.sub(r'<script\b[^>]*\bdata-knowledge-map="[^"]*"[^>]*>\s*</script>','',text)
  text=re.sub(r'<script\b[^>]*\bsrc="[^"]*knowledge-neighborhood\.js[^"]*"[^>]*>\s*</script>','',text)
  for css in ['knowledge-map.css','knowledge-reader-shell.css','knowledge-neighborhood.css']:
   text=re.sub(r'<link\b[^>]*\bhref="[^"]*'+re.escape(css)+r'[^"]*"[^>]*>','',text)
   text=text.replace('</head>',f'<link rel="stylesheet" href="/study-site/{css}?v={version(css)}"></head>',1)
  tags=f'<script src="/study-site/knowledge-map.js?v={version("knowledge-map.js")}" defer data-knowledge-map="/study-site/{data_path}?v={version(data_path)}"></script>'
  tags+=f'<script src="/study-site/knowledge-neighborhood.js?v={version("knowledge-neighborhood.js")}" defer></script>'
  text=text.replace('</body>',tags+'</body>',1);(SITE/reader).write_text(text)
  rows.append({'chapterId':chapter,'title':title,'readerPath':reader,'knowledgeMapPath':data_path,'readerPageCount':count,'nodeCount':len(data['nodes']),'startPage':min(p for n in data['nodes'] for p in n['pages'])})
 (SITE/'knowledge-map-registry.json').write_text(json.dumps({'schemaVersion':1,'maps':rows},ensure_ascii=False,indent=2)+'\n')
 cards=''.join(f'<section class="card"><h2>{escape(x["title"])}</h2><p>{x["readerPageCount"]}个真实课件页 · {x["nodeCount"]}个概念节点</p><a class="primary" href="/study-site/{x["readerPath"]}?map=1#p{x["startPage"]:02d}">打开常驻知识图谱</a></section>' for x in rows)
 (SITE/'knowledge-maps.html').write_text('<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>知识图谱 · 课程伴学</title><link rel="stylesheet" href="/study-site/course-hub.css"></head><body><main><nav class="course-nav"><a href="/study-site/courses.html">学习首页</a><a href="/study-site/communications.html">通原目录</a><a href="/study-site/network.html">计网目录</a></nav><header><h1>从概念连线回到真实课件页</h1><p>节点连线展示先修、对比与应用关系；切到概念清单可搜索。点击页码后图谱仍然保留，讲义与原图同步跳转。</p></header>'+cards+'<aside class="note">这里只列本批已接入的图谱，不把预览镜像重复计数。翻页不会自动标记已读；你的原学习进度保持独立。</aside></main></body></html>')
 print(f'Integrated {len(rows)} maps')
if __name__=='__main__':main()
