#!/usr/bin/env python3
"""Build the isolated Homework 4 lesson and answer sheets. No shared navigation writes."""
from pathlib import Path
from html import escape
import json

ROOT = Path(__file__).resolve().parents[1]
SITE = ROOT / 'site'
ASSETS = SITE / 'assets/data-structures-homework4'
ASSETS.mkdir(parents=True, exist_ok=True)
BASE = '/study-site/'
TREE = {'A': ['B','F'], 'B': [None,'C'], 'C':['D','E'], 'D':[None,None], 'E':[None,None], 'F':[None,'G'], 'G':['H',None], 'H':[None,None]}
HUFF = {'r': ['17','24'], '24':['9','15'], '9':['4s','5'], '15':['7','8'], '4s':['2a','2b'], '7':['3','4']}
WEIGHTS = {'r':41,'24':24,'9':9,'15':15,'4s':4,'7':7,'17':17,'5':5,'8':8,'2a':2,'2b':2,'3':3,'4':4}
MERGES = [(2,2,4,[3,4,4,5,8,17]),(3,4,7,[4,5,7,8,17]),(4,5,9,[7,8,9,17]),(7,8,15,[9,15,17]),(9,15,24,[17,24]),(17,24,41,[41])]

def traverse(node, order):
    if node is None: return ''
    l,r=TREE[node]
    parts = {'N':node, 'L':traverse(l,order), 'R':traverse(r,order)}
    return ''.join(parts[c] for c in order)

assert traverse('A','NLR') == 'ABCDEFGH'
assert traverse('A','LNR') == 'BDCEAFHG'
assert traverse('A','LRN') == 'DECBHGFA'

def make_tree(kind):
    if kind == 'traversal':
        pos={'A':(380,48),'B':(180,148),'F':(550,148),'C':(270,248),'G':(640,248),'D':(195,348),'E':(345,348),'H':(565,348)}
        children=TREE; width,height=780,410
        label={x:x for x in pos}; title='由中序 BDCEAFHG 与后序 DECBHGFA 唯一确定的二叉树'
        desc='A 的左孩子 B、右孩子 F；B 只有右孩子 C；C 的左孩子 D、右孩子 E；F 只有右孩子 G；G 只有左孩子 H。'
    else:
        pos={'r':(260,48),'17':(100,148),'24':(480,148),'9':(310,248),'15':(650,248),'4s':(220,348),'5':(400,348),'7':(570,348),'8':(780,348),'2a':(160,448),'2b':(280,448),'3':(510,448),'4':(630,448)}
        children=HUFF; width,height=880,520
        label={k:str(v) for k,v in WEIGHTS.items()}; label.update({'2a':'2₁','2b':'2₂'})
        title='权值 8、2、5、3、2、17、4 的一棵哈夫曼树'
        desc='根 41 的孩子是 17 和 24；24 的孩子是 9 和 15；9 的孩子是内部结点 4 和叶子 5；内部结点 4 的孩子是两个权值 2；15 的孩子是 7 和叶子 8；7 的孩子是叶子 3 和叶子 4。'
    out=[f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" role="img" aria-labelledby="{kind}-title {kind}-desc" class="tree-svg" data-tree="{kind}"><title id="{kind}-title">{escape(title)}</title><desc id="{kind}-desc">{escape(desc)}</desc>', '<style>.tree-edge{stroke:#74938a;stroke-width:2.5;fill:none}.tree-node circle{fill:#f1f6ee;stroke:#487669;stroke-width:2}.tree-node text{stroke:none;fill:#183e43;font:600 23px system-ui,sans-serif;text-anchor:middle;dominant-baseline:central}.tree-node.leaf circle{fill:#245f58;stroke:#245f58}.tree-node.leaf text{fill:white}.tree-side{font:15px system-ui,sans-serif;fill:#4e6761;text-anchor:middle;paint-order:stroke;stroke:#fffef9;stroke-width:5;stroke-linejoin:round}.tree-node.is-visited circle{fill:#d9e9de;stroke:#356c58}.tree-node.is-visited text{fill:#173b32}.tree-node.is-current circle{fill:#f1c96b;stroke:#825e19;stroke-width:4}.tree-node.is-current text{fill:#3a2a0b}.tree-foot{font:16px system-ui,sans-serif;fill:#4e6761;text-anchor:middle}</style>']
    for node, kids in children.items():
        for side,child in zip(['左','右'], kids):
            if child is None: continue
            x,y=pos[node]; X,Y=pos[child]
            out.append(f'<path class="tree-edge" d="M{x},{y} L{X},{Y}" data-parent="{node}" data-child="{child}" data-side="{side}"/>')
            if kind=='traversal': out.append(f'<text class="tree-side" x="{(x+X)/2}" y="{(y+Y)/2-7}">{side}</text>')
    for node,(x,y) in pos.items():
        leaf = not any(children.get(node,[]))
        out.append(f'<g class="tree-node{" leaf" if leaf else ""}" transform="translate({x} {y})" data-node="{node}"><circle r="26"/><text>{label[node]}</text></g>')
    foot='先序：A → B → C → D → E → F → G → H' if kind=='traversal' else '深绿色：原始叶子权值　浅色：合并得到的内部结点'
    out.append(f'<text class="tree-foot" x="{width/2}" y="{height-15}">{foot}</text></svg>')
    return ''.join(out)

traversal_svg=make_tree('traversal'); huffman_svg=make_tree('huffman')
(ASSETS/'traversal-tree.svg').write_text(traversal_svg)
(ASSETS/'huffman-tree.svg').write_text(huffman_svg)

boundary_svg='''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 840 255" data-tree="boundary" role="img" aria-labelledby="boundary-title boundary-desc"><title id="boundary-title">最后一个非叶子结点与第一个叶子结点</title><desc id="boundary-desc">499 有孩子 998 和 999；500 有孩子 1000 和 1001；501 没有孩子，编号 1002 和 1003 已超出总结点数。</desc><style>[data-tree="boundary"] text{font:19px system-ui,sans-serif;text-anchor:middle;fill:#183e43;stroke:none}[data-tree="boundary"] path{fill:none;stroke:#74938a;stroke-width:2.5}[data-tree="boundary"] .node{fill:#f1f6ee;stroke:#487669;stroke-width:2}[data-tree="boundary"] .leaf{fill:#245f58;stroke:#245f58;stroke-width:2}[data-tree="boundary"] .light{fill:white}[data-tree="boundary"] .ghost{fill:none;stroke:#adb6b0;stroke-width:2;stroke-dasharray:5 5}[data-tree="boundary"] .muted{fill:#6d7b76;font-size:16px}</style><path d="M140 66L80 162M140 66L200 162M420 66L360 162M420 66L480 162"/><path d="M700 66L640 162M700 66L760 162" stroke-dasharray="5 5"/><circle class="node" cx="140" cy="66" r="32"/><circle class="node" cx="420" cy="66" r="32"/><circle class="leaf" cx="700" cy="66" r="32"/><text x="140" y="73">499</text><text x="420" y="73">500</text><text class="light" x="700" y="73">501</text><circle class="leaf" cx="80" cy="162" r="32"/><circle class="leaf" cx="200" cy="162" r="32"/><circle class="leaf" cx="360" cy="162" r="32"/><circle class="leaf" cx="480" cy="162" r="32"/><circle class="ghost" cx="640" cy="162" r="32"/><circle class="ghost" cx="760" cy="162" r="32"/><text class="light" x="80" y="169">998</text><text class="light" x="200" y="169">999</text><text class="light" x="360" y="169">1000</text><text class="light" x="480" y="169">1001</text><text class="muted" x="640" y="169">1002</text><text class="muted" x="760" y="169">1003</text><text class="muted" x="420" y="224">最后一个双孩子结点</text><text class="muted" x="700" y="224">超过 1001，不存在</text></svg>'''
(ASSETS/'complete-tree-boundary.svg').write_text(boundary_svg)

q1_answer='''第1题
按层序从1开始连续编号，结点i的左、右孩子编号分别为2i、2i+1。
叶子结点满足2i>1001，故编号为501～1001，共1001−501+1=501个。
度为2的结点满足2i+1≤1001，即i≤500，共500个。
若结点只有左子树，则2i≤1001<2i+1，因而2i=1001，不可能成立，故为0个。
答：叶子结点501个，度为2的结点500个，只有左子树的结点0个。'''
q2_answer='''第2题
中序：BDCEAFHG；后序：DECBHGFA。
后序最后一个结点A是根；由中序分出左子树BDCE、右子树FHG。
对应后序分别为DECB、HGF，故左右子树的根分别为B、F。
递归划分后：B只有右孩子C；C的左、右孩子为D、E；F只有右孩子G；G只有左孩子H。
二叉树：
        A
       / \\
      B   F
       \\   \\
        C   G
       / \\ /
      D  E H
先序遍历（根—左—右）：A B C D E F G H，即ABCDEFGH。
复核：中序BDCEAFHG，后序DECBHGFA，与题设一致。'''
q3_answer='''第3题
权值：8、2、5、3、2、17、4。把两个权值2分别记作2₁、2₂。
每次合并当前最小的两个权值：
2₁+2₂=4；3+4（原始叶子）=7；4（合并结点）+5=9；
7+8=15；9+15=24；17+24=41。
一棵哈夫曼树如下（方括号表示原始叶子）：
             41
            /  \\
         [17]   24
               /  \\
              9    15
             / \\   / \\
            4  [5] 7  [8]
           / \\    / \\
        [2₁][2₂][3] [4]
以根到叶子经过的边数为路径长度：17的长度为1，8、5的长度为3，2₁、2₂、3、4的长度为4。
WPL=17×1+8×3+5×3+2×4+2×4+3×4+4×4=100。
也可用合并权值之和校验：WPL=4+7+9+15+24+41=100。
同权结点的选择顺序、左右分支交换可产生其他正确的哈夫曼树，最小WPL仍为100。'''
all_answers='数据结构与算法基础 · 作业4\n\n'+ '\n\n'.join([q1_answer,q2_answer,q3_answer])+'\n\n说明：答案仅保存在学习网站，未向课程平台提交。\n'
(SITE/'data-structures-homework4-answers.txt').write_text(all_answers)

def fig(svg, caption, name):
    return f'<figure class="tree-figure"><div class="figure-scroll" tabindex="0" aria-label="树图，可横向滚动">{svg}</div><figcaption>{caption} <a href="{BASE}assets/data-structures-homework4/{name}.svg" target="_blank" rel="noopener">打开大图</a></figcaption></figure>'

def copybox(idx, text):
    return f'<div class="copy-answer"><div class="copy-heading"><strong>可抄作业版</strong><button type="button" class="js-only" data-copy="copy-q{idx}">复制第{idx}题答案</button></div><pre id="copy-q{idx}">{escape(text)}</pre></div>'

q1=f'''
<section class="homework-question" id="q1" aria-labelledby="q1-title">
<header><p class="eyebrow">QUESTION 01 · COMPLETE BINARY TREE</p><h2 id="q1-title">1001 个结点，怎样数叶子？</h2></header>
<div class="original-question"><h3>题目</h3><p>一棵完全二叉树有 1001 个结点，求叶子结点数、度为 2 的结点数，以及只有左子树的结点数。</p></div>
<div class="answer-grid"><div><span>叶子结点</span><strong>501</strong></div><div><span>度为 2</span><strong>500</strong></div><div><span>仅有左子树</span><strong>0</strong></div></div>
<h3>先把三个名称分清楚</h3>
<ul><li><strong>叶子结点：</strong>没有孩子，度为 0，数量记作 n<sub>0</sub>。</li><li><strong>度为 2 的结点：</strong>左右孩子都存在，数量记作 n<sub>2</sub>。这里的“度”只数孩子，不把连向父亲的边算进去。</li><li><strong>只有左子树：</strong>左孩子存在、右孩子不存在。在完全二叉树里，度为 1 只能是这种情况；不可能“只有右孩子”。</li></ul>
<p><strong>完全二叉树的关键：</strong>除最后一层外，前面各层都填满；最后一层从左往右连续填，不留空位。因此可以从 1 开始按层连续编号。</p>
<h3>方法一 · 用编号找分界，最直观</h3>
<div class="formula">结点 i 的左孩子：2i；右孩子：2i + 1。<br>编号不超过 1001 才代表实际存在。</div>
<ol class="reasoning"><li><strong>先找最后一个有孩子的结点。</strong>结点 500 的孩子是 1000 和 1001，都存在；结点 501 的左孩子应为 1002，已超过范围。所以 1～500 是非叶子，501～1001 全是叶子。</li><li><strong>数叶子时别漏掉端点。</strong>从 501 到 1001 是一段连续编号，共 <span class="math">1001 − 501 + 1 = 501</span> 个。</li><li><strong>数度为 2 的结点。</strong>右孩子存在的条件是 <span class="math">2i + 1 ≤ 1001</span>，即 <span class="math">i ≤ 500</span>，所以有 500 个。</li><li><strong>检查有没有“只填了左边”的结点。</strong>所有非叶子结点 1～500 都已经有两个孩子，所以只有左子树的结点是 0 个。</li></ol>
{fig(boundary_svg,'这是编号分界附近的局部示意，不是把 1001 个结点全部画出。虚线位置不存在。','complete-tree-boundary')}
<details><summary>方法二 · 用 n₀ = n₂ + 1 与奇偶性，更适合考试</summary>
<p>对任意非空二叉树都有 <span class="math">n<sub>0</sub> = n<sub>2</sub> + 1</span>。在完全二叉树中，度为 1 的结点最多只有一个，而且只能是最后一个非叶子结点。</p>
<div class="formula">1001 = n<sub>0</sub> + n<sub>1</sub> + n<sub>2</sub> = 2n<sub>2</sub> + n<sub>1</sub> + 1。<br>所以 1000 = 2n<sub>2</sub> + n<sub>1</sub>。</div>
<p>右边的 2n<sub>2</sub> 是偶数，因此 n<sub>1</sub> 必须是偶数；又因 n<sub>1</sub> 只能取 0 或 1，故 n<sub>1</sub> = 0。于是 n<sub>2</sub> = 500，n<sub>0</sub> = 501。</p>
<p><strong>为什么 n₀ = n₂ + 1？</strong>一棵有 n 个结点的树有 n − 1 条边。按父结点数边，又有 n − 1 = n<sub>1</sub> + 2n<sub>2</sub>。与 n = n<sub>0</sub> + n<sub>1</sub> + n<sub>2</sub> 相减，即得结论。</p>
<p class="pitfall">“奇数个结点就没有度为 1 的结点”只在<strong>完全二叉树</strong>条件下成立。普通二叉树不能这样推。</p>
</details>
<details><summary>方法三 · 按层数叶子，解释为什么不是 490</summary>
<p>前 9 层填满共有 <span class="math">2<sup>9</sup> − 1 = 511</span> 个结点。第 10 层有 <span class="math">1001 − 511 = 490</span> 个，都是叶子。</p>
<p>这 490 个结点占满第 9 层前 245 个父结点的左右孩子。第 9 层共有 256 个结点，余下 <span class="math">256 − 245 = 11</span> 个也没有孩子，也是叶子。所以总叶子数是 <span class="math">490 + 11 = 501</span>，不能只数最下一层。</p>
</details>
<div class="checkpoint"><strong>一眼自检：</strong>501 + 500 + 0 = 1001；501 = 500 + 1。两条都符合。</div>
{copybox(1,q1_answer)}
<p class="source-note">课件依据：第五章 PDF <a href="{BASE}data-structures-ch5.html#p02">第 2 页（定义与 n₀ = n₂ + 1）</a>、<a href="{BASE}data-structures-ch5.html#p03">第 3 页（层序编号与孩子编号）</a>。</p>
</section>'''

q2=f'''
<section class="homework-question" id="q2" aria-labelledby="q2-title">
<header><p class="eyebrow">QUESTION 02 · REBUILD A BINARY TREE</p><h2 id="q2-title">中序 + 后序：先找根，再分左右</h2></header>
<div class="original-question"><h3>题目</h3><p>已知二叉树的中序遍历为 <code>BDCEAFHG</code>，后序遍历为 <code>DECBHGFA</code>。画出二叉树，并求其先序遍历。</p></div>
<div class="answer-box"><span class="label">先序遍历</span><p class="big-sequence">A B C D E F G H</p><p>连写为 <strong>ABCDEFGH</strong>。这是重建得到的结果，不是把字母直接排序。</p></div>
<h3>只记住这两句话</h3>
<div class="two-rules"><div><span>后序：左 → 右 → 根</span><strong>最后一个字母是当前子树的根。</strong></div><div><span>中序：左 → 根 → 右</span><strong>根左边属于左子树，根右边属于右子树。</strong></div></div>
<p>切开中序后，知道左、右子树各有多少个结点，再按同样的数量切开后序。对每一小段重复这一规则。题中各结点字母互不重复，因此可唯一确定。</p>
<h3>第 1 步 · 找整棵树的根 A</h3>
<div class="split-line"><span class="left-sub">B D C E</span><strong>A</strong><span class="right-sub">F H G</span><small>中序：左子树 4 个　|　根　|　右子树 3 个</small></div>
<div class="split-line"><span class="left-sub">D E C B</span><span class="right-sub">H G F</span><strong>A</strong><small>后序：按 4 个、3 个、1 个切开</small></div>
<p>于是 A 的左子树根是 <strong>B</strong>（DECB 的末尾），右子树根是 <strong>F</strong>（HGF 的末尾）。</p>
<h3>第 2 步 · 递归拆开，特别留意空子树</h3>
<div class="table-scroll" tabindex="0"><table><caption>每行都是一次“后序找根、中序分边”</caption><thead><tr><th scope="col">当前中序</th><th scope="col">当前后序</th><th scope="col">根</th><th scope="col">左侧中序</th><th scope="col">右侧中序</th><th scope="col">得到的结构</th></tr></thead><tbody><tr><td>BDCEAFHG</td><td>DECBHGFA</td><td>A</td><td>BDCE</td><td>FHG</td><td>A 左 B，右 F</td></tr><tr><td>BDCE</td><td>DECB</td><td>B</td><td>∅</td><td>DCE</td><td>B 只有右孩子 C</td></tr><tr><td>DCE</td><td>DEC</td><td>C</td><td>D</td><td>E</td><td>C 左 D，右 E</td></tr><tr><td>FHG</td><td>HGF</td><td>F</td><td>∅</td><td>HG</td><td>F 只有右孩子 G</td></tr><tr><td>HG</td><td>HG</td><td>G</td><td>H</td><td>∅</td><td>G 只有左孩子 H</td></tr></tbody></table></div>
<p>D、E、H 所在的小段都只剩一个字母，所以它们直接成为叶子。∅ 表示空子树，不需要再建结点。</p>
<h3>第 3 步 · 画出树，再按“根 → 左 → 右”读</h3>
{fig(traversal_svg,'连线已标明左、右。B→C 和 F→G 是右孩子；G→H 是左孩子，三处不要画反。','traversal-tree')}
<div class="walkthrough js-only" id="traversal-player"><h4>在同一棵树上，逐个检查三种遍历</h4><div class="player-controls"><label for="traversal-order">遍历方式</label><select id="traversal-order"><option value="pre">先序 · 根左右</option><option value="in">中序 · 左根右</option><option value="post">后序 · 左右根</option></select><button type="button" data-traversal="prev">上一步</button><button type="button" data-traversal="next">下一步</button><button type="button" data-traversal="reset">重置</button></div><p id="traversal-status" role="status">点击“下一步”访问第一个结点。</p><div id="traversal-sequence" class="sequence-chips" aria-label="遍历输出"></div><p class="small">黄色圈是当前访问结点，浅绿色圈是已访问结点。只演示访问顺序，不写入学习记录。</p></div>
<p>先输出根 <strong>A</strong>；接着完整走左子树，得到 <strong>B C D E</strong>；最后完整走右子树，得到 <strong>F G H</strong>。拼接即 <strong>A + BCDE + FGH = ABCDEFGH</strong>。</p>
<div class="checkpoint"><strong>把结果反查回题设：</strong><br>中序：(B D C E) A (F H G) = BDCEAFHG；<br>后序：(D E C B) (H G F) A = DECBHGFA。两个序列同时吻合。</div>
<details><summary>常见卡点：为什么 B 没有左孩子？为什么 G 的孩子在左边？</summary><p>只看这棵<strong>当前子树</strong>的中序：<code>B | DCE</code> 中 B 的左边为空，所以 B 没有左子树。类似地，<code>F | HG</code> 说明 F 没有左子树；<code>H | G</code> 说明 H 在 G 的左侧，因此是 G 的左孩子。</p><p>后序只能告诉你根是谁，<strong>左右方向必须结合中序</strong>决定。不要看到“单孩子”就随手画在左边。</p></details>
{copybox(2,q2_answer)}
<p class="source-note">课件依据：第五章 PDF <a href="{BASE}data-structures-ch5.html#p04">第 4 页（三种遍历定义）</a>、<a href="{BASE}data-structures-ch5.html#p05">第 5 页（遍历序列重建二叉树）</a>。</p>
</section>'''

merge_rows=''
for i,(a,b,c,rest) in enumerate(MERGES,1):
    detail='先合并两个原始权值 2' if i==1 else ('此处选原始叶子 4' if i==2 else ('此处用第 1 步生成的 4' if i==3 else ''))
    merge_rows+=f'<tr data-merge-step="{i}"><th scope="row">{i}</th><td>{a} + {b} = <strong>{c}</strong></td><td>{", ".join(map(str,rest))}</td><td>{detail or "重新排序后继续选最小两个"}</td></tr>'
q3=f'''
<section class="homework-question" id="q3" aria-labelledby="q3-title">
<header><p class="eyebrow">QUESTION 03 · HUFFMAN TREE</p><h2 id="q3-title">哈夫曼树：每次只合并最小的两个</h2></header>
<div class="original-question"><h3>题目</h3><p>给定权值 <code>8, 2, 5, 3, 2, 17, 4</code>，构造哈夫曼树，并求其带权路径长度 WPL。</p></div>
<div class="answer-box"><span class="label">最小带权路径长度</span><p class="big-result">WPL = 100</p><p>图的左右方向不唯一；正确构造得到的最小 WPL 相同。</p></div>
<h3>先认识 WPL：权值乘距离，再相加</h3>
<p>题目给的 7 个权值是<strong>7 个叶子</strong>的权值，不能把它们直接放成 7 个任意结点。权值 2 出现两次，必须保留两个叶子，以下记为 2₁、2₂。</p>
<div class="formula">WPL = Σ（叶子权值 w<sub>i</sub> × 从根到该叶子的边数 ℓ<sub>i</sub>）</div>
<p>路径长度数的是<strong>边</strong>，不是经过的结点数。根的路径长度是 0；根的直接孩子为 1。若把根记作第 1 层，那么路径长度 = 所在层数 − 1。</p>
<p><strong>构造口诀：</strong>把当前各棵树的根权值排好序，拿出最小两个作为兄弟，生成一个权值为二者之和的新父结点，把新权值放回候选集合，重新比较。一直合并到只剩一棵树。</p>
<h3>第 1 步 · 六次合并，每一次都重新排序</h3>
<p>初始排序：<code>2₁, 2₂, 3, 4, 5, 8, 17</code>。7 棵单结点树合成 1 棵，需要 <strong>7 − 1 = 6 次</strong>合并。</p>
<div class="table-scroll" tabindex="0"><table><caption>同权值的选择采用固定示例：第 2 步先选原始叶子 4</caption><thead><tr><th scope="col">步</th><th scope="col">本次合并</th><th scope="col">合并后候选权值（从小到大）</th><th scope="col">说明</th></tr></thead><tbody>{merge_rows}</tbody></table></div>
<div class="pitfall"><strong>第 2 步为什么还有两个 4？</strong>一个是题目本来给的叶子 4，另一个是 2₁ + 2₂ 生成的内部结点 4。它们权值相同但不是同一个结点，不能去重。</div>
<h3>第 2 步 · 从最后一次合并往下画</h3>
<p>最后的 <span class="math">17 + 24 = 41</span> 决定根是 41；24 再拆成 9 和 15；依次还原每一步合并关系，就得到下面这棵树。</p>
{fig(huffman_svg,'深绿色的 7 个叶子恰好对应题目给的权值。内部的 4 是 2₁ + 2₂；右下角的 4 是原始叶子。','huffman-tree')}
<h3>方法一 · 按叶子计算 WPL，最稳妥</h3>
<div class="table-scroll" tabindex="0"><table><caption>路径长度按图中从根出发经过的边数计算</caption><thead><tr><th scope="col">叶子权值</th><th scope="col">从根到叶子的路径</th><th scope="col">边数 ℓ</th><th scope="col">权值 × 边数</th></tr></thead><tbody><tr><th scope="row">17</th><td>41 → 17</td><td>1</td><td>17</td></tr><tr><th scope="row">8</th><td>41 → 24 → 15 → 8</td><td>3</td><td>24</td></tr><tr><th scope="row">5</th><td>41 → 24 → 9 → 5</td><td>3</td><td>15</td></tr><tr><th scope="row">3</th><td>41 → 24 → 15 → 7 → 3</td><td>4</td><td>12</td></tr><tr><th scope="row">4（原始）</th><td>41 → 24 → 15 → 7 → 4</td><td>4</td><td>16</td></tr><tr><th scope="row">2₁</th><td>41 → 24 → 9 → 4 → 2₁</td><td>4</td><td>8</td></tr><tr><th scope="row">2₂</th><td>41 → 24 → 9 → 4 → 2₂</td><td>4</td><td>8</td></tr></tbody><tfoot><tr><th colspan="3" scope="row">WPL</th><td><strong>100</strong></td></tr></tfoot></table></div>
<div class="formula">WPL = 17×1 + 8×3 + 5×3 + 3×4 + 4×4 + 2×4 + 2×4<br>= 17 + 24 + 15 + 12 + 16 + 8 + 8<br>= <strong>100</strong>。</div>
<h3>方法二 · 把六次合并的结果相加，快速复核</h3>
<div class="formula">WPL = 4 + 7 + 9 + 15 + 24 + 41 = <strong>100</strong>。</div>
<details><summary>为什么“合并值之和”恰好等于 WPL？</summary><p>合并权值为 a、b 的两棵树时，给它们添一个共同父结点。这两棵树的<strong>所有叶子距离新根都增加 1</strong>，带权路径长度因此增加 a + b。</p><p>从 7 棵单叶树开始，每棵树的初始路径长度都是 0。六次合并累加出的 WPL 增量，就是 4、7、9、15、24、41。因此它们的总和等于最终 WPL。这也等于“所有内部结点权值之和”，但不能再加一次原始叶子权值。</p></details>
<details><summary>同学画出的树不一样，是否一定错？</summary><p>不一定。每个内部结点的左右孩子互换，叶子的路径长度不变；遇到相同权值，也可以采用另一种合法的选择。</p><p>例如第 2 步可以用 <span class="math">3 +（2₁ + 2₂）= 7</span>，再把原始叶子 4 与 5 合成 9。这样两个 2 的路径长度变为 5，原始 4 的路径长度变为 3，但仍有：</p><div class="formula">17×1 + 8×3 + 5×3 + 4×3 + 3×4 + 2×5 + 2×5 = 100。</div><p>所以应检查<strong>每次是否选了当前最小两个</strong>、原始叶子是否齐全、WPL 是否按自己的图计算，不能只看图是否与示例一模一样。</p></details>
<div class="checkpoint"><strong>最后四项自检：</strong><ul><li>根权值：8 + 2 + 5 + 3 + 2 + 17 + 4 = 41。</li><li>叶子 7 个，内部结点 6 个，共 13 个结点。</li><li>每个内部结点恰好有两个孩子，没有度为 1 的结点。</li><li>按叶子计算与按合并值计算，都得到 WPL = 100。</li></ul></div>
{copybox(3,q3_answer)}
<p class="source-note">课件依据：第五章 PDF <a href="{BASE}data-structures-ch5.html#p08">第 8 页（路径长度、WPL 与哈夫曼树）</a>、<a href="{BASE}data-structures-ch5.html#p09">第 9 页（构造步骤与非唯一性）</a>。本题权值未归一化，不把 WPL = 100 误写成平均码长。</p>
</section>'''

head='''<!doctype html>
<html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="description" content="数据结构作业4：完全二叉树1001结点计数，中序后序重建二叉树，哈夫曼树与WPL。逐步推导、准确树图和可抄答案。"><title>{title}</title><link rel="stylesheet" href="/study-site/course-hub.css"><link rel="stylesheet" href="/study-site/data-structures.css?v=20261102"><link rel="stylesheet" href="/study-site/data-structures-homework4.css?v=20261114"></head><body class="{body_class}"><a class="skip-link" href="#main">跳到正文</a><main id="main"><nav class="hw4-local-links" aria-label="数据结构作业导航"><a href="/study-site/data-structures.html#homework">← 数据结构作业</a><a href="/study-site/data-structures-ch5.html">第五章原课件</a></nav>'''
foot='''<footer><p>数据结构与算法基础 · 作业4 · 2026-11-14</p><p>按用户提供的三道题整理，已核对第五章原课件的定义与约定。只保存学习内容，不连接或提交课程平台。</p></footer></main><p id="copy-status" role="status" class="copy-status" hidden></p><script src="/study-site/data-structures-homework4.js?v=20261114" defer></script></body></html>'''
lesson=head.format(title='作业4 · 二叉树与哈夫曼树 · 数据结构伴学',body_class='hw4-lesson')+'''
<header class="hw4-hero"><p class="eyebrow">DATA STRUCTURES · HOMEWORK 04</p><h1>从“数结点”，<br>到亲手把树画出来。</h1><p class="lede">完全二叉树、遍历重建、哈夫曼树。每题先给结论，再从定义走到答案；画图不省略左右方向，计算都有第二种检查办法。</p><div class="actions"><a class="primary" href="/study-site/data-structures-homework4-answers.html">可抄答案 / 打印</a><a class="button" href="/study-site/data-structures-homework4-answers.txt" download>下载纯文本答案</a></div><p class="save-notice">已保存到学习网站 · 未向课程平台提交</p></header>
<nav class="hw4-route" aria-label="三题目录"><a href="#q1"><span>01 / 完全二叉树</span><strong>501 · 500 · 0</strong><small>编号分界 + 性质法 + 按层复核</small></a><a href="#q2"><span>02 / 遍历重建</span><strong>ABCDEFGH</strong><small>逐层拆分 + 完整树图 + 遍历演示</small></a><a href="#q3"><span>03 / 哈夫曼树</span><strong>WPL = 100</strong><small>六次合并 + 两种 WPL 计算</small></a></nav>
<aside class="reading-tip"><strong>怎么用这一页：</strong>先看每题绿色结果框；不懂时沿着步骤往下走。要抄写时使用题末“可抄作业版”，要打印时打开独立答案页。扩展方法和易错点可以按需展开。</aside>
'''+q1+q2+q3+foot
(SITE/'data-structures-homework4.html').write_text(lesson)

answer_html=head.format(title='作业4 · 可抄答案与树图 · 数据结构伴学',body_class='answer-sheet hw4-answers')+'''
<header><p class="eyebrow">HOMEWORK 04 · ANSWER SHEET</p><h1>数据结构与算法基础 · 作业4</h1><p class="identity-line">姓名：____________　学号：____________　班级：____________</p><p class="no-print">包含必要推导、树图与最终答案；网站保存不等于课程平台提交。</p></header><div class="actions no-print"><button type="button" data-print class="js-only">打印 / 另存为 PDF</button><a class="button" href="/study-site/data-structures-homework4-answers.txt" download>下载答案 TXT</a><a href="/study-site/data-structures-homework4.html">返回逐题讲解</a></div>
<section class="homework-question" id="q1"><h2>第 1 题 · 完全二叉树结点数</h2><p>已知完全二叉树共有 1001 个结点，按层序从 1 开始连续编号，结点 i 的左、右孩子编号分别为 2i、2i + 1。</p><ol><li>叶子结点满足 2i &gt; 1001，所以编号为 501～1001，共 <strong>501 个</strong>。</li><li>度为 2 的结点满足 2i + 1 ≤ 1001，即 i ≤ 500，共 <strong>500 个</strong>。</li><li>只有左子树须满足 2i ≤ 1001 &lt; 2i + 1，即 2i = 1001，不可能成立，故有 <strong>0 个</strong>。</li></ol><p><strong>答：叶子结点 501 个，度为 2 的结点 500 个，只有左子树的结点 0 个。</strong></p></section>
<section class="homework-question" id="q2"><h2>第 2 题 · 由遍历序列重建二叉树</h2><p>中序：BDCEAFHG；后序：DECBHGFA。</p><p>后序最后一个结点 A 为根。由中序分出左子树 BDCE、右子树 FHG，对应后序分别为 DECB、HGF，故左右子树根分别为 B、F。继续划分得：B 只有右孩子 C；C 的左、右孩子为 D、E；F 只有右孩子 G；G 只有左孩子 H。</p>
'''+fig(traversal_svg,'二叉树如图，连线标明左、右孩子。','traversal-tree')+'''
<p>先序遍历按“根 → 左 → 右”，所以先序序列为 <strong>A B C D E F G H</strong>，即 <strong>ABCDEFGH</strong>。</p><p>复核：中序 BDCEAFHG，后序 DECBHGFA，均与题设一致。</p></section>
<section class="homework-question" id="q3"><h2>第 3 题 · 哈夫曼树与带权路径长度</h2><p>权值为 8、2、5、3、2、17、4。将两个权值 2 分别记为 2₁、2₂。</p><p>每次合并当前最小的两个权值：</p><div class="formula">2₁ + 2₂ = 4；3 + 4（原始叶子）= 7；<br>4（合并结点）+ 5 = 9；7 + 8 = 15；<br>9 + 15 = 24；17 + 24 = 41。</div>
'''+fig(huffman_svg,'一棵正确的哈夫曼树。深绿色为题目给出的原始叶子。','huffman-tree')+'''
<p>从根到叶子的路径长度按<strong>边数</strong>计：17 的长度为 1；8、5 的长度为 3；2₁、2₂、3、4 的长度为 4。</p><div class="formula">WPL = 17×1 + 8×3 + 5×3 + 2×4 + 2×4 + 3×4 + 4×4<br>= <strong>100</strong>。</div><p>用内部结点权值之和校验：<strong>WPL = 4 + 7 + 9 + 15 + 24 + 41 = 100</strong>。</p><p class="small">哈夫曼树不一定唯一；同权结点的不同选择以及左右分支交换可得到其他正确的树，最小 WPL 仍为 100。</p></section>
'''+foot
(SITE/'data-structures-homework4-answers.html').write_text(answer_html)

fixtures={'assignment':'data-structures-homework4','complete':{'n':1001,'n0':501,'n1':0,'n2':500},'traversal':{'root':'A','children':TREE,'inorder':'BDCEAFHG','postorder':'DECBHGFA','preorder':'ABCDEFGH'},'huffman':{'root':'r','children':HUFF,'weights':WEIGHTS,'original_leaves':['8','2a','5','3','2b','17','4'],'merge_sums':[x[2] for x in MERGES],'wpl':100},'source':{'file':'第五章树和二叉树（不含线索树）(2).pdf','sha256':'f793d81fbc2e70eae16a5c4063d9a116e24f19f31468d0ab74179cbbc1f584d6','pdf_pages':[2,3,4,5,8,9]}}
(ROOT/'tests/data-structures-homework4-fixtures.json').write_text(json.dumps(fixtures,ensure_ascii=False,indent=2)+'\n')
print('Built Homework 4 lesson, answer HTML/TXT, 3 SVG assets and fixtures.')
