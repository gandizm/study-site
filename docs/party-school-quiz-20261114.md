# 党校随机刷题接入

- 科目入口：`party-school.html`，练习页：`party-school-quiz.html`。
- 添加第六科“党校学习”，仍以 `study-catalog.json` 和导航生成器作为首页、全站科目导航的来源。
- 刷题不是指定作业，没有新增 assignments，也没有替换首页的通信原理第五章最新作业。
- 135题题号连续，每题3个选项；嵌入题库载荷与此前已发布版本完全一致。原始DOCX不公开。
- 原题未附答案。133题另据权威文本核对；20/27题仍为 ambiguous/null，不计入正确率或错题本。每题有解释与来源。
- 随机不重复、点选立即反馈、下一题、整轮总结、错题本、复习移出、学习记录均保留。
- 存储键仍为 `party-school-quiz-135-v1`；本站和原独立站不同域，记录不会自动迁移。不改原五科存储键或脚本。
- `?preview=1` 只用内存，不读写已有学习记录；损坏或不可读取的已有刷题记录不会被静默覆盖。
- 公开站点不要求ChatGPT登录。未加入后端、统计追踪或作答上传。

## 验证

运行 `python3 scripts/build-study-navigation.py`、`python3 tests/study-navigation.test.py`、`node tests/party-school-quiz.test.cjs` 和原部署所列课程检查。仅把与本任务有关的源文件纳入提交；全站导航由部署阶段生成，旧课程正文/资源/记录逻辑不变。
