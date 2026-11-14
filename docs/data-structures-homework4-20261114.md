# 数据结构作业4：二叉树与哈夫曼树

## 发布范围

- `site/data-structures-homework4.html`：三题逐步讲解、三张准确 SVG、可展开的补充方法、三种遍历逐步演示、逐题复制。
- `site/data-structures-homework4-answers.html`：独立可抄答案及打印布局；包含完整二叉树与哈夫曼树图。
- `site/data-structures-homework4-answers.txt`：纯文本答案，含 ASCII 树图。
- `site/data-structures-homework4.css`、`.js`：仅影响本次页面，无网络请求、个人记录存储或课程平台操作。
- `site/assets/data-structures-homework4/`：独立 SVG 文件，可打开大图。
- `scripts/build-data-structures-homework4.py`：可重复生成页面、图与数学 fixtures，不修改公共导航。

本次保留作业3、8章原课件与其他课程，不替换已有学习记录。网站保存不代表向作业平台提交。

## 数学核对

1. 完全二叉树 n=1001：叶子501、度2结点500、只有左子树0。编号法、性质/奇偶性法以及按层计数一致。叶子不只在最下一层：第10层490个加第9层11个。
2. 中序 BDCEAFHG，后序 DECBHGFA：根A；A左B右F；B只有右C；C左D右E；F只有右G；G只有左H。先序 ABCDEFGH。回算中序和后序均符合。
3. 权值8,2,5,3,2,17,4：合并值4,7,9,15,24,41；WPL=100。两个2保留为不同叶子，原始叶子4和内部权值4明确区分。同权另一选择的WPL也为100。

## 已核对的真实课程来源

第五章树和二叉树（不含线索树）(2).pdf，共9个PDF物理页。
SHA-256：`f793d81fbc2e70eae16a5c4063d9a116e24f19f31468d0ab74179cbbc1f584d6`。

- PDF第2、3页：完全二叉树定义、n0=n2+1与层序编号。
- PDF第4、5页：先中后序的定义与由遍历序列重建二叉树。
- PDF第8、9页：路径长度以边数计，WPL定义、哈夫曼树构造及非唯一性。

已直接检查以上6页的渲染图，而非只凭文字抽取。新题的条件来自本次用户给定题目，不声称它们原样出现在课程PDF中。

## 验证命令

```sh
python3 scripts/build-data-structures-homework4.py
python3 tests/data-structures-homework4.test.py
node tests/data-structures-homework4-ui.test.cjs
node --check site/data-structures-homework4.js
```

- 数学测试独立枚举1～2001个结点的完全二叉树，独立重建中后序树，核验全部左右孩子。
- 独立最小堆核验哈夫曼最优合并值，校验原始叶子、叶深、内部权值和SVG实际连线。
- 页面检查：本次页面本地链接存在、ID唯一、复制目标与资源存在、没有外部依赖。
- UI单测运行实际脚本：三种遍历全部8步、前后边界、重复点击、重置、切换、当前/已访问状态；复制成功/失败回退、打印、独立答案页无播放器分支。
- 以上自动检查已通过。最终浏览器视图和Pages精确提交部署结果由本次整合发布记录补充，不把单测冒充浏览器验收。

## 公共导航整合

只需新增catalog记录，再使用现行 `scripts/build-study-navigation.py` 生成导航、科目归档和两个相同首页。不要直接把旧首页覆盖到远端。本次与电磁场新作业同时整合，最终发布以重新核实的远端HEAD为基线。

所有新增文件可在现有构建工作流的“Validate data structures courseware and homework”后补充运行两项新增测试。生成页面后再运行导航生成器，以补回统一导航。
