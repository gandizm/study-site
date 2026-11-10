# 通信原理第5—7章两遍辅导

## 发布范围

- 新主入口：`site/communications-course-redraw.html`，4个总览单元＋第5章12单元＋第6章10单元＋第7章12单元。
- 作业入口：`site/communications-ch5-homework.html`，5.9.1、3、9、13、14、15、20、25。
- 原课件对应141、116、125页，原教材扫描不新增公开。每单元区分原PPT页、书内印刷页和PDF文件页。
- 首页、课程首页、通原目录和材料说明新增入口，不替换旧课程或旧逐页伴读。

## 阅读与内容约定

默认第一遍只读必学和代表题，第二遍折叠。一次展示一个单元，原图按需回查；数学式为静态MathML，教学图为同源SVG。主导航、上一节/下一节和浏览器前后退均以hash定位，不修改旧学习记录。作业可逐题阅读，也可展开全部题目。复制功能仅操作本地剪贴板，不发送问题、答案或学习数据。

第14题的折叠二进制不等同于Gray码；第15题使用自然段内码。误差统一采用输入减重建，第9题保留两种量程口径，第20题说明有效编码边界，第25题分别求第一零点带宽和理想无码间干扰最小带宽。

## 构建与校验

内容源：`docs/communications-lessons/*.md`。以Pandoc和lxml构建：

    python scripts/build-communications-lessons.py
    python scripts/build-communications-figures.py
    python tests/communications-lessons.test.py
    node --check site/communications-redraw.js

新增校验包含章节与题号完整性、MathML存在、默认折叠、唯一ID与本地链接/图、前导零码组和无进度存储写入。另独立核算三角谱重叠、接收均衡、量化、A律、增量调制、TDM、升余弦抽样点和QPSK映射。公开部署仍须检查精确commit及对应Pages运行，再检查线上交互与视觉效果。

既有文件除入口与部署测试外不改写；无需迁移任何旧进度键。公开目录中不得放入个人记录、凭据、浏览器配置或教材扫描件。
