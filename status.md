# 项目状态 (status.md)

> **规格基准见 `prd.md`**（背景/结构/数据契约/实现逻辑以 PRD 为准）。本文件只记录**进度快照**。
> 更新：2026-09-13(R50) · 负责人：Kurt

---

## 一句话现状

**PAC + Identity 阶段 🟢 冻结(用户 R50 架构级裁定);Resolver Consumer Adversarial Audit 两轮闭环(R53 第一轮 + R54 第二轮边界攻击,均经用户/裁定收口)。R53 验收(用户裁定):"没有证明 Resolver 正确,而是证明 Resolver 按冻结契约实现时没有发现违反契约的行为"——Reference Resolver 继续保持审查对象,不进入生产链路。R54 落地:F1 Structural Consistency Check(Audit Invariant only,非 Gate 非 admission rule;source_version_sha/行号/span hash 四项;88 份真实语料控制组 2403/2403 单元 0 漂移)+ 二轮攻击 R-ACC-12/13/14(结构合法但语义错误 13/13 全链绿 → 语义正确性归宿 = Admission 层获量化坐实;material 消费零重塑;unresolved 消费不变量 0 findings,下游默认值攻击面 596 槽位已登记)。0 新生 resolver 缺陷。**R55(用户令:对 R45 声明严格对抗性复证,逐结论真实测试):顶层声明全部成立(族级一致 78/78;"0 新缺陷"为分诊结论而非语料无缺陷证明的边界已量化);新发现 F-r55-2 = R46 更正自身分项缺口(23≠24,漏计 c12-02 Q20),F-r55-3 = 分项数字非事实层(三套分类桶界互异)。**下一步待裁定:P1 BUG-11/14/15 数据卫生 / basis schema-only(已批,仅检测→PENDING_REVIEW)/ R55 收口。**身份唯一来源 = manifest v2 字段;三边界纪律维持:Resolver 只做 structural 判断、Gate 只证明约束、PENDING_REVIEW 通道不得为提 PASS 率扩展自动规则。审计治理:Input Integrity Gate + Audit Snapshot Manifest(`R50_input_baseline@sha256:795ee1e7…beb`,356 文件)。readiness 声明按 `review_protocol.md` 规则 2 三列举证;恢复/成功类声明按规则 4 报 numerator/denominator/proof method。

---

## 当前阶段

**阶段:PAC + Identity 冻结(R50)→ Resolver Consumer Adversarial Audit 两轮闭环(R53 第一轮实现级审查 + 用户验收 🟢;R54 第二轮边界攻击)→ 待用户裁定下一轮**。阶段证据链:PAC 22 份全链 → R47 架构级验收 → R48 契约纸面冻结 → R49 审查体系可信度攻击 → R50 冻结裁定 + 审计治理机制 → R51 治理轮对抗收口 → R52 参考 Resolver 实现(严格按冻结契约,不进生产链路)→ R53 第一轮(R-ACC-1~11 全过,独立重算 0 findings,变异 15/15)→ 用户验收裁定(F1 实施=Audit Invariant only;STALE 边界不扩大;进入第二轮)→ **R54:F1 落地(88 份控制组 2403/2403 单元 0 漂移)+ R-ACC-12/13/14 边界攻击(语义错误 13/13 全链绿量化坐实 Admission 必要性;material 零重塑;unresolved 不变量 0 findings)**。三十一中化学 keep 三方裁决独立挂起;数据卫生轮已启动(用户裁定序 11→14→15):**R58 BUG-11 ✅ 修复**(recover_images 扫描白名单废弃→排除派生目录单一来源制;视野 2,421→3,119,新可见 698;实测盲区当前缺图候选=0,危害定性为流程潜伏风险;+5 回归钉/双变异咬合/184 passed+1 xfailed);下一项 = BUG-14(未分类跑步机 + 73 重复源);其后 ③ basis schema-only(已批准,detection-only)→ ④ printed 硬化。

---

## 已完成里程碑

- ✅ **方案定型**：锚点式批注（源不动、只插锚点、LLM 只输出行号）；根本规则 R1–R12 逐条确认（PRD §5）。
- ✅ **重切流水线** `reslice_pipeline.py`（v2.1 嵌套格式）：行号化→mimo-x-pro-preview→确定性校验→三产出，支持 `--resume`/`--recompile`。
- ✅ **试点 16/16 通过**：九大学科 × 三学段，用户全部签核；`reslice_qc.py` C1–C10 全绿（`data/reslice_pilot_qc.json`：16 PASS / 0 FAIL）。对比 v6 全量基线合格率 4.0%，路线成立。
- ✅ **全库源缺陷量化** `corpus_scan.py`（3120 份）：双重识别 138 份/148 处；裸 LaTeX 954 份（简单 4918 / 复杂 610）。
- ✅ **配图恢复** `recover_images.py`：43,463 张（0.64 GB），原始 md 与 v6 悬空引用已修复；目录覆盖 BUG-11 已修复（R58：视野 2,421→3,119，排除派生目录制，见 bugs.md）。
- ✅ **渲染质检** `render_lint.py` / `render_preview.py`：修复 32 处 `alt="Image"" />` 损坏 + 2 处字面货币 `$`；LaTeX/表格结构整体良好；消费方需开 mhchem（`\ce{}` 3 处 / 2 份化学卷）。
- ✅ **溯源比对器** `pdf_fidelity.py`：已建+验证，但**精度不足仅粗筛**（实证高假阳性，见 PRD §10-G）。

### 人工审核签核（试点 16 份，全部通过）

| 状态 | 文件 | 备注 |
|---|---|---|
| ✅ | 高一\数学\2021顺义一中（下）期中 | 首份，格式清晰 |
| ✅ | 高一\英语\2020东城（上）期末 | 完形嵌套模型（material⊂questions）确立 |
| ✅ | 高一\语文\2020平谷五中（下）4月月考 | 阅读复合题嵌套验证 |
| ✅ | 高一\化学\2021三十一中（下）期中 | 修 Q27 双重识别、Q39 丢行（PDF 文本层回填） |
| ✅ | 高一\地理\2019人大附中（上）期中 | 复合题最密集（16个）全过 |
| ✅ | 高一\生物\2018西城（下）期末 | 图表/遗传题验证 |
| ✅ | 高一\政治\2018师大附中（下）期中 | 材料分析题/长段答案验证 |
| ✅ | 高一\语文\2020石景山（上）期末 | 修 material 边界 + 切片嵌套重复 bug |
| ✅ | 高一\历史\2021四十三中（上）12月月考 | 已知源缺陷（4题答案缺失）确认为忠实反映 |
| **里程碑** | **高一 9/9 全科通过** | 重切路线成立 |
| ✅ | 高二\物理\2019四中（下）期末 | 首份高二卷 |
| ✅ | 高二\数学\2018五十六中（下）期中（理） | 修 Q8 图文错序、Q9 配图漂移(extra 改卫星锚) |
| **里程碑** | **高二 2/2 通过** | |
| ✅ | 高三\物理\2021石景山一模 | 高考难度物理通过 |
| ✅ | 高三\化学\2019交大附中（上）12月月考 | 修裸 LaTeX(18+2)、丢图×2(PDF 提取补回) |
| ✅ | 高三\数学\2021八十中考前练习 | 公式/图形完整，无缺陷 |
| ✅ | 高三\生物\2020西城（上）期末 | 修 Q20(3) 伪标题 `##` |
| ✅ | 高三\英语\2021丰台二模 | **16/16 试点全部通过** |
| **里程碑** | **试点 16/16 全过** | 九科×三学段全验证，进入全量推广决策 |

> 审核中确立并固化进流水线：unit 包络不进答案区、锚点同点 LIFO 闭合、综合题整块化+material 嵌套、extra 配图漂移通道、C10 锚点配对。
> **角色归类约定**：评分标准/细则类归 **answer 区**（提示词 R3 + 规则 9 固化；试点 4 处验证一致）。

---

## 进行中

- ⏳ **源修复批**（须在全量重切前做，让 LLM 看到干净源）：
  - 裸 LaTeX 已自动修 **4388 行**（可回滚 `data\bare_latex_fix_log.json`）；**BUG-09 已修复**（R5 收紧 TOKEN 引入的 103 行半包已回退 + 加防回归，见 `bugs.md`）；残留 715 行复杂 + 105 行括号式待半自动。
  - **新发现 BUG-15（既存，待定）**：全库"半定界"数学（`$` 岛 + 岛外裸命令）**1490 份 / 23,221 行**，corpus_scan/fix_bare_latex 双双跳过 `$` 行故此盲区；是数/化/生的**主要数学债**，需半自动整段定界，量大须先小样验证。
  - 双重识别 148 处（difflib 已定位，待逐个删）。
- ⏳ OCR 后台转换：守护运行中（用户手动启动），队列 12703 份，撞 20000 页/日自动等午夜续跑。

---

## 全量推广前准备清单

- [ ] 源修复收尾：715 复杂裸 LaTeX + 148 双重识别 + **BUG-15 剩 table/BLOCK/COMPLEX≈1030 留档待人工**（R15 两轮审查后仅 SPACE 453 有效零误改；TABLE 已回滚）。（BUG-09 的 103 行已回退✅）
- [x] ~~锚点 LIFO 死逻辑 / 守护 stdout PIPE 死锁 / OCR token 外部化~~（R9 修 BUG-10/12/13 ✅，见下）；剩 图片恢复目录扩列（BUG-11）。
- [ ] 数据卫生：去重 73 份重复源、周期重归类 `未分类`（现存 145 且仍在接收）、归档 `.restored.md`。
- [ ] `reslice_pipeline` 加**全量 runner**（枚举全库 + 吞吐/配额控制；现 CLI 仅试点版）。
- [x] **大文件冒烟 + 50 份测速批（R17 完成）**：49/50 成功、44 零校验问题；xlarge 6717 行 23 万 prompt tokens 一次过（不需拆卷）；实测 186 万 tokens / 3.9h（串行 290s/份）；外推全量 ≈1.1 亿 tokens、串行 9.8 天 → 全量需并发。剩：几何(1) IncompleteRead、extract_json 无重试缺陷。
- [ ] 全量重切（v2.1）+ QC C1–C10 回归 + 渲染预览抽查（需先定并发方案）。
- [ ] **入库 Resolver 前置任务（R19 决策）**：答案表单元格级切分——14 份 304 unit 的 answer_lines 指向单行 `<table>`，入库时按题号解析对应 td，每题只挂自己的答案格；切片层保持现状。
- [ ] 待用户给 Phase I-4「42 ambiguous target」定义 → 设计 manifest 对照验证 → 定 Phase I-5。

---

## 风险登记（详见 PRD §10）

| 级别 | 项 | 摘要 |
|---|---|---|
| 🟡 | **BUG-15 半定界数学（部分修复）** | 真实仅 1476 行（旧 23221 系把 `$$`块误算）；**R15 两轮对抗审查后仅 SPACE 453 有效零误改**（岛外`\quad`→空格，3 处 `$` 错乱误改已回滚）；**TABLE 376 已回滚**（blind replace 拆坏 `\nearrow`）；table/BLOCK/COMPLEX≈1030 留档待人工，不阻塞测试 |
| 🟠 | **BUG-16 EOL 静默转换（工具，R16 已修代码）** | `write_text` 在 Windows 把原 LF 文件整文件转 CRLF；证据链闭合（语料 1280 LF / 被碰 469 全 CRLF / 同目录对照）；下游影响实测 0；代码已 `newline=""`+单测；**历史数据无快照不可精确恢复**（嫌疑分桶 中205，未做概率恢复） |
| 🟡 | 全量 runner / 吞吐已定价（R17 C 批） | 50 份实跑：49/50 成功、44 零问题；xlarge 6717 行一次过（不需拆卷）；外推全量 ≈1.1 亿 tokens/串行 9.8 天 → 需并发；剩 1 份几何(1) IncompleteRead + extract_json 无重试待修 |
| 🟢 | **阶段一完成（R23）** | v2.1 工具链交付：prompt v2.1（题前图/答案行）+extract_json 重试+并发 runner（--workers）+修复链一键串行；全流程测试抓出 7 缺陷全修（--out 账目联动/429 指数退避/max_tokens 50000/行号越界截断等）；压测 9/10、8 路 93.4s/份（3.2×）、修复链幂等。残留：政治汇编（三）超长输出三轮败于服务端，全量时特殊处理。**待决策：全量启动（workers 数/启动时间）** |
| 🟢 | **测试套件 + CI（R26/R27）** | R26 响应 ChatGPT 第一轮审查：固化 pytest 套件（全离线）+ GitHub Actions CI；可测性重构（clamp_intervals/rel_out 提取、fixer 加 --out/--log）；conftest 合成试卷 fixture。**R26 声称"CI 就绪"被第二轮审查证伪（H-01：import 期硬依赖开发机私有配置，CI collection 全灭 0 用例执行）**；R27 修复（ROOT 去硬编码+配置惰性加载+渲染路径与配置解耦）并补 no-config 回归 3 用例、fake-LLM E2E 1 用例、bug 形状测试改 strict xfail；mutation 验证 3 组（M1/M2/M3 破坏生产代码均被测试咬住）。现 30 passed + 1 xfailed；真 LLM 冒烟通过。**CI 已实测绿灯：GitHub Actions Run 34669715877（969dad6）= success，`30 passed, 1 xfailed in 0.63s`**。 |
| ✅ | ~~调试跑覆盖正式账目~~ | BUG-21 已修复（R28：derive_run_paths 纯函数，--out 账目/日志一律派生隔离；附带修账目目录假定存在；4 回归用例含真实子进程集成，M4 mutation 验证咬住）。套件 34 passed + 1 xfailed |
| 🟡 | 未分类跑步机 / 图片目录落后 | 剩 BUG-11/14（数据卫生与覆盖），长跑/全量前处理 |
| ✅ | ~~LIFO 死逻辑 / stdout 死锁 / token 明文~~ | BUG-10/12/13 已修复（R9：单测+recompile/QC 16/16+加载验证） |
| ✅ | ~~裸 LaTeX 半包残损~~ | BUG-09 已修复（R8：103 行回退 + 加防回归，`data\bug09_revert_log.json`） |
| 🔵 | status.md 曾自相矛盾 | 本次已重写；PRD 为唯一规格基准 |
| 🟡 | **BUG-22 题号重复归属（R30 发现 / R31 修复 Phase 1 / R32 分层记账）** | 8/50 真实产物大题内编号被当全卷题号;根因确诊为 prompt v2.1"分节照抄"条款主动指示(定性:Prompt Specification Defect)。R31:① C13 升级 **Scoped Question Identity**((section,题号),选考模块/汇编合法重号放行);② Prompt v2.2(题号以答案区键位为准 + section 字段);③ 确定性迁移 `fix_bug22_renumber.py`(answer_key/shift/keep + migration report)。**迁移后 batch-C QC:C13 残留 0,38/50 PASS**。第五轮审查裁定:Prompt/QC/迁移三层 🟢 CLOSED,**resolver identity model 与 V3 canonical identity 🟡 OPEN**——设计评审稿 `question_identity_design.md`(R32)待验收后进入 Phase 2 实施。**R33 更正:QC detection 层口径受限**——scoped C13 对 BUG-22 回归形态漏放 6/7,见 BUG-23 |
| 🟢 | **第五轮外部审查(R31 验收)** | **Phase 1 🟢 PASS / ACCEPTED**:完整证据链(真实缺陷→根因→prompt 纠偏→存量迁移→审计留痕→回归)获认可;mutation 验证评为"测试可信度 Strong";batch-C QC 解释自洽(Before→Guard→Fix→Restore 闭环)。指令:**先 Phase 2(QuestionIdentity 模型)、再 Phase 3(对抗语料证明)、最后才讨论全量 rollout** |
| 🟢 | **BUG-23 C13 Guard Soundness Failure(R33 发现 / R34 修复)** | 回迁突变实测:BUG-22 原始回归形态(跨分节重号)在保留 section 时仅 1/7 被生产 C13 拦截。R34 修复:QuestionIdentity v2 划分语义(非 keep 全卷唯一 + keep 个体豁免须带可回源证据,证据不足 → PENDING_REVIEW);batch-C 50 份确定性回填 v2(0 fail);**复验:回迁突变 7/7 全拦、缺 section 8/8 显式告警**。证据 `data/phase2_adversarial_review_r34.json` |
| 🟢 | **Phase 2 QuestionIdentity 实施(R34)** | 四项一体落地:basis 字段 + SectionLocator schema(612 locators)+ C13/C14 v2 三态裁决 + 存量确定性回填(50/50,printed provenance:source_line 948 / migration 134 / unknown 402 猜测禁止)。**P2-01~P2-08 全部有真实测试**(`tests/test_question_identity_phase2.py`,64 passed + 1 xfailed);回填后 batch-C QC 38 PASS 零回归。残留:v1 历史产物(pilot)旧语义待回填;basis_evidence 语义充分性待 Phase 3 对抗语料 |
| 🟢 | **Phase 3 Evidence Soundness(R35)** | 第五轮审查验收 R34(Phase 2 🟢 ACCEPTED / BUG-23 🟢 CLOSED)后执行:第二层证据语义检查(evidence 引用行必须承载编号语义且题号相关,prose/噪声/无关题号 → PENDING_REVIEW,不越界宣称语义真值);真实 batch-C 复验 **0 新增 review**;对抗语料 `test_identity_adversarial_corpus.py` **16/16**(含核心攻击 c09 证据行无编号语义 / c10 证据题号无关 / c11 OCR 内容错 + c16 回填幂等字节一致);变异验证短路语义检查恰被 c09/c10/c11 拦截。套件 **80 passed + 1 xfailed**。残留:证据语义真值走 PENDING_REVIEW 人工通道(按裁定为 obligation 非 BUG) |
| 🟢 | **pilot v1→v2 迁移清尾(R36)** | 第五轮审查裁定 Identity 层冻结后的收尾:16 份纯 v1 试点卷确定性迁移(`phase3_pilot_v1_migration.py`,零 LLM,迁移后四条自检+违规回滚),**15/16 applied / 0 violations**,迁移后 QC 与 v1 基线**裁决零翻转**(15 PASS/1 FAIL),字节级幂等 15/15,事实快照 389 单元入库;验收测试 10/10 含变异 sanity(伪造 printed/事实漂移/同节 keep 重号全拦)。**残留:三十一中化学被 C13 如实拒写 → 根因为 BUG-24(见下),决策点上报** |
| 🟢 CLOSED | **BUG-24 分节标题过滤器误杀(R36 发现 / R37 修复 / R38 复核 / R39 用户裁定关闭)** | `_heading_rows` 的 `答案\|解析\|评分` 排除器整行子串匹配,误杀含 note 的真实分节标题(三十一中化学 L324 填空题节)→ SectionLocator 假阴性。修复:排除器两阶段结构角色识别(结构归一化 + 归一头部窗口 10 判 marker)。**三概念分账(不得混写)**:① BUG-24 correctness = CLOSED;② 3 例 straddle 跨界标题 = ACCEPTED KNOWN BOUNDARY(扩窗 11 实测误杀合法标题,不硬修);③ 1 例 OCR 行融合 = ACCEPTED OCR LIMITATION。"heading detection 问题全部解决"无证据不成立。保留独立决策点:三十一中化学 Q1-11/F1-11 keep 三方裁决(不得自动豁免) |
| 🟢 CLOSED | **BUG-25 `\.` 转义点误升(R38 发现并修复,用户裁定 FIX VERIFIED)** | OCR 转义点 `26 \.` 击穿 `_NUM_PREFIX` 序号前缀剥离 → 8 例【答案】/【解析】块被误升为分节标题(全部 full-corpus 非提交范围,提交产物零影响)。修复后恢复面 848→840(恰减 8),66 份提交 manifest 字节零变化,4 条真实行入回归语料。明细 `bugs.md` BUG-25 |
| 🟢 | **BUG-24 修复全链复验(R37)** | 改码前先锁影响面:before 快照(bug24_locator_snapshot)+ before QC 与 R34 提交基线逐文件零差异;全语料盘点 3120 卷:恢复 848 行(reslice-scope 恢复 13 行逐条人检:6 真分节 + 7 benign 源结构标题)。~~"全语料 0 答案内容行误升"~~ **该全称主张已被 R38 证伪并正式撤销(RETRACTED),正确口径见下行**。修复后:**11 份 manifest 重生成**(batch-C 7 + pilot 4,三十一中如实拒写故字节不变),**QC 裁决集零翻转**(38/12、15/1),fails 全部 0→0,字节级幂等 66/66,NEW-OLD diff `data/bug24_fix_report.json`;验收 `tests/test_bug24_section_locator.py` B24-01~08 + 三类变异 sanity |
| 🟢 ACCEPTED | **R38 对抗性审查(用户最终裁定:高质量 adversarial review)** | 8 攻击面独立复核:A2 issue 明细零差异(66/66)、A3 事实漂移 0、A4 他目录 v2 存量 0、A6 新增 start_line 恰等于 13 条恢复行且丢失 heading 0(集合级归因证明)、A7 数字逐位复现——通过且证据强于 R37;**A1 证伪"全语料 0 误升"过强主张** → BUG-25 修复;4 例残留裁定 ACCEPTED KNOWN LIMITATION;补 `--refresh-v2` FACTS 锚点守卫 3 测试(含变异注入)。正确口径:**提交范围 13 行 0 误升(逐条人检);全语料 840 行含 4 例已知残留(0.5%)**。套件 **106 passed + 1 xfailed**,审计工件 `data/r38_audit_report.json` |
| 🔵 | **R39 冻结候选基线登记 + 审查协议建立(2026-09-13 用户裁定)** | `7f37be9 / R38` = **Identity v2 + SectionLocator 冻结候选基线**,Identity 层不再扩展规则;项目阶段切换 System Readiness Gate。新审计规则入库 `review_protocol.md`:规则 1 全称命题必须穷尽验证(触发词:全部/零/没有/唯一/所有/无遗漏/无误升/全量保持)、规则 2 readiness claim 三列(claim/证据域/证据类型)+ 禁止"局部 PASS→系统 PASS"、规则 3 既有方法论六条汇总。R37 全称主张正式 RETRACTED 记档。**R40 已对抗性复核** |
| 🟢 ACCEPTED(R41 用户裁定) | **R39 结论对抗性审查(R40)** | 16 攻击面全部真实测试:基线 diff 零生产代码、CI 复查、套件重跑 106+1、收集口径 bare==scoped(变异对照)、norecursedirs 投毒目录功能测试(变异对照)、"CI 一直 tests/" git 历史穷举、三概念分账三处落盘、**BUG-25 全语料记账九数字逐位复现**(3120/44211/11747/10907/10899/840/848/75/13;`3045=3120−75 reslice 源`结构性闭合)、8 条 `\.` 行逐一复验现被排除、窗口边界实测(『答案』跨第 10~11 字符,10 保留/11 误杀)、**BUG-25 变异验证**(回退转义点→B24-02 咬住)、66/66 manifest sha256==快照。**发现 3 处措辞/落盘问题当场修正**:① R39"空目录"无证据资格(证据只支持"ACL 不可读");② bugs.md 缺显式 RETRACTED(已补);③ "marker 恰在第 9 位"1 基不精确(已改"跨第 10~11 字符")。**限定措辞(R41 用户裁定采纳):R40 独立复核范围内,R39 的实质工程结论未发生结论级翻转;发现 3 项证据表达或台账完整性问题,均已修正并复验("原报告完全无错误 = false" 同时成立)。** 用户裁定同时明确:R40 ACCEPTED ≠ 系统冻结,readiness gate 尚未开始 |
| 🔵 IN PROGRESS | **System Readiness Gate 正式启动(R41 用户裁定)** | 从局部缺陷对抗升级为**端到端系统不变量对抗**,四个一级攻击面:A 生产路径完整性(Input→preprocessing→artifact→manifest→QC→identity→handoff:字段丢失/schema 漂移/v1v2 混用/忽略工件依赖/fresh checkout 不可运行/生产数据与 fixture 语义不一致);B 失败传播(FAIL/PENDING_REVIEW/MISSING/STALE 是否可被后续阶段静默转 PASS);C 工件可追溯性(Source→Output→QC→Fix→Snapshot 完整回溯,防"产物正确但无法证明为什么正确");D Fresh 环境可复现(fresh clone+无隐藏本地语料+无忽略工件+无预存在目录,R36 事故为一级攻击面先例)。Gate 不重复 R40。三十一中化学 keep 三方裁决独立保留,不与 readiness 混为同一问题。**R41 第一轮实测完成**:A schema 80/80 零缺陷(生产 66 = 65 v2 + 1 已知 v1);B **发现 BUG-26(`--recompile` 洗 v2 身份头)→ 修复 + mutation 验证**;降级爆炸半径实测 0 裁决翻转(如实量化);PENDING/FAIL 优先级正确;C 重编译字节确定性 0 不一致;**C-01 过期证据工件已刷新**(pilot QC json 停留 R25 记三十一中 PASS,现实为 FAIL,现 15 PASS/1 FAIL);D fresh checkout 套件全绿(89 passed/17 skipped/1 xfailed),D-02 9 个脚本(10 处)硬编码路径记硬化待办。证据 `data/r41_gate_ac_report.json`/`data/r41_gate_b02_report.json` |
| 🟢 ACCEPTED(2026-09-13 用户裁定) | **R41 结论对抗性审查(R42)** | 14+2 攻击面全部真实测试:套件/CI 复验、BUG-26 变异重做(补丁式恢复,mutation locality evidence:恰好 2 条新测试 FAIL、邻近 9 条不受影响)、**B-02 模拟升级为真实 check()**(65 份落盘降级副本,0 翻转证实)、CLI 级 recompile+幂等+v1 兼容、**重编译确定性与 QC 对账双双升级为 80 份穷举**(0 不一致/0 漂移,口径限定"defined scope = 80 份当前目标工件",不外推任意未来输入)、值域审计、C-01 刷新工件 sha256 可复现、**fresh checkout 新 HEAD 9240a1c 重验(91/17/1,17 skip 全带 corpus 理由;精确口径="当前 HEAD 在缺失相应 corpus 时 fresh checkout 可重复,skip 均有明确 corpus 缺失原因",不得简化为"全部通过")**、B-03 泛化、顶层键型穷举(无 BUG-26 同类盲区)。**抓到 2 新问题**:BUG-27(basis 词表三处不一致+`explicit` 游离,文档勘误完成)+ D-02 计数勘误(正式口径 **9 个文件 10 个引用点**);**披露补全**:stress10 4 FAIL / test-v21 2 FAIL(测试语料,非交付范围)入账。**用户裁定:R42 = Identity/SectionLocator/Recompile/QC Stability 最后一次审查闭环,审查递归就此终止**。明细 `log.md` R42 |
| 🟢 APPROVED(R50 用户裁定,实施排期③) | **basis 值域机器校验(CONTRACT ENFORCEMENT CANDIDATE,非 BUG)** | R42 值域审计发现 `check_identity` 不校验 basis 值域(任意字符串可流通)。R47 修订:实施方向 = schema validation only。**R50 正式批准实施,严格限定三条:① 只做 invalid enum detection;② 非法值 → schema violation surfaced as PENDING_REVIEW(不得转 FAIL);③ 不得静默 PASS**——否则改变历史数据裁决语义。实施排期按用户优先序第 ③ 位(Resolver 消费审查轮与 BUG-11/14/15 之后);测试最低覆盖 valid/invalid/missing/null/empty/case/whitespace/unknown-future。决策矩阵原文 `question_identity_design.md` §10.7 |
| 🟢 ACCEPTED(R47 用户架构级复核) | **R31–R46 审查链验收 + 阶段切换(2026-09-13 用户裁定)** | 用户(声明:证据链层复核,非独立代码重扫)裁定:R46 = 整个审查链证据等级最高一轮,**作为 Identity+PAC 阶段结束标志**;组件表 Identity v2/SectionLocator/C13-C14/migration-backfill/PAC 审计框架全 🟢,Resolver 消费 🟡 下一阶段风险,Resolver→IR 🔴 未审。**采纳三条规则化建议**:① BUG-29 评级 🟡 Medium,升级为统一 **ArtifactWriter Contract 治理候选**(禁直接写死工件路径,writer 控制 output root/overwrite/atomic/backup,并入 D-02 同族扫描面,实施待批);② **review_protocol 新增规则 4**:恢复/成功类声明必须报 numerator/denominator/proof method(出处 c09-01 printed 23/34 事件);③ 三边界纪律固化:Resolver 只做 structural 判断、Gate 只证明约束、PENDING_REVIEW 通道不得为提 PASS 率扩展自动规则。**优先序(用户)**:① Gate+Resolver Boundary → ② BUG-11/14/15 → ③ basis 值域(schema-only)→ ④ printed 硬化(unknown > guessed)。**决策点上报**:resolver 实体 NOT_BUILT,"Resolver 消费 v2 对抗性审查"开审前须用户裁定审查对象(契约纸面审 / 实现后审)。明细 `log.md` R47 |
| 🟢 ROUND-1 DONE(2026-09-13) | **Gate 首攻面:Production Adversarial Corpus 第一轮实测(R44)** | 设计稿 `production_adversarial_corpus_design.md`。用户批准(26 目标/本轮 PDF 类 22 份/OCR 直调 API)后执行:22 份真实源选样指纹留档(测量纠偏 2 处推定:换真扫描件+融合第二例实证);**OCR 22/22(293 页,与实测逐份相等)**;**LLM 22/22(57.7 万 tokens)**;pipeline 原生 v1 → 生产同款回填 **22/22 v2(0 fail/0 review)**;**QC 18 PASS/4 FAIL**(4 FAIL 全部可解释:c07-01 BUG-17 家族/c09-01 源面答案缺失/c09-02 结构行混入/c11-02 融合后果,无一静默);**OCR 漂移量化:0/22 字节一致(相似 0.955–1.000)、转义点 hazard 逐行复现、答案行标题化随机漂移(c06-02 12 处/c10-02 6 处)且下游 QC 鲁棒**;BUG-25 修复在全新数据 0 误升;c09-01 printed/canonical 分离正确(BUG-22 prompt v2.3 生效)。全 stage 轨迹 `data/pac_track_round1.json`(resolver/compiler/gate/admission 如实 NOT_BUILT);**Gate 发现:pipeline 原生输出 v1,消费 v2 必须经回填步骤**(resolver 契约约束+rollout 流程清单)。**R45 补齐:22/22 深度语义复核**——语义探针(R30 校准)530 单元 78 报警逐条分诊 = 76 探针盲区 + 2 源卷版本噪音(c13-02 题干区『1小题』vs 解析区『2小题/编号10-11』,resolver 契约须知:answer 区编号可与题干区不一致),**0 新缺陷**;题号覆盖 10/10 完美(0 缺号 0 重号);发现 printed 回收边界(c01-02 括号式题号 `(1)(2)` → 28/28 unverified,正则只认 `NN.`,硬化候选待决策)。**R46 对抗性审查(用户令:逐结论真实测试复证)通过**:track 数字独立重算 550 项 0 不一致(293 页/577,225 tokens/530 单元/18/4/78 全复证);QC 真实产物变异 17/17 命中(14 检查族无失敏);探针双向变异 8/8 + 78 报警独立再分诊(规则 54 + 人工读原文 24)→ **"0 新缺陷"成立**,更正 R45 分项计数(65+2≠78)与 c09-01 printed 措辞(23/34 recovered);BUG-29 补 CI 回归(+19 测试,套件 130 passed);hazard 形态逐条复证(转义点 L266/274、L445/461 同位复现 0 误升;c05-01 转义点升节定性为解答题标题设计行为非答案块误升)。残留:C3 DOCX/C4 图像 BLOCKED;第二轮扩样待用户分诊裁定 |
| 🟢 ACCEPTED(R56 二审裁定收口) | **R55:R45 声明对抗性复证(逐声明真实测试)** | 8 项声明逐条复证:探针账目(530/78/11,P13:24+P14:32+P15:22)独立重算+重放全等;**"0 新缺陷"顶层命题成立**(新写独立分类器三方交叉:标签级 43/78 全为同族桶界差异,族级一致 **78/78 跨族 0**;残差 24 条逐条机器证据分诊);c13-02 源卷噪音行级证据坐实;覆盖 22/22 全量穷举全完美(含具名 30/30、44/44、34/34);c01-02 28/28 unverified + 正则根因逐行验证(阳性对照命中);track 22/22 深度字段级可证(人类阅读过程声明如实限定);R45 套件 111+1xfail 经 294f5c7 worktree 离线重跑 94+17skip+1xfail 算术闭合 + CI Run 34723840150 success。**新发现 F-r55-2:R46 对 R45 的更正自身分项缺口(残差分项和 23≠24,漏计 c12-02 Q20)**;F-r55-3:分项数字非事实层,族级账目+逐行留档为准。变异 5 组全咬合(工件删报警/真实语料答案值篡改→QC+探针全绿的结构链边界量化/工具自身代码变异 3 项);R50 基线 verify 0 漂移。R55 工具自身缺陷 3 项当场修(F-r55-4)。工具 `scripts/r55_r45_audit.py`,CI +9,套件 175 passed + 1 xfailed |
| 🟢 裁定已落地(R57) | **外部架构级审核意见(R31–R55 链)+ 二审裁定** | 审核方自述边界:基于台账材料、非代码级扫描。唯一可测断言(审计/测试复杂度超过生产核心)经实测**成立**:冻结生产链 1,351 行 vs 审计家族 ~4,400 行 + 测试 2,882 行 ≈ 5.4 倍(定性:维护成本风险,非正确性风险)。**二审裁定(R56):R55 收口 ✅;G-TAX-1+Rule Retirement Policy、G-RES-1、G-BOUND-1 立即采纳;G-SCHEMA-1 延期至 IR vNext(不反向改 Identity v2);G-AUD-1 暂不实施(历史脚本=provenance)**。R57 已落地:`governance/rule_registry.md`(五类 taxonomy + 每规则 purpose/attack surface/evidence/retirement + 退役政策 5 条)、契约附录 D(Resolver 四项禁令:semantic inference/similarity/knowledge classification/answer correctness;阶段定位=Data Admission Layer;审计惯性防线)、CI +4 双向钉住(代码↔登记册 set-diff)+ 变异咬合验证。**下一阶段路线(用户):Identity v2 冻结 → BUG-11/14/15(序 11→14→15)→ basis schema-only → Admission 稳定化 → V3 Backend 消费** |
| 🟢 FIXED(R58,数据卫生轮 1/3) | **BUG-11 图片恢复扫描目录覆盖落后于重归类** | 修复:`recover_images.py` 白名单 `SCAN_DIRS` 废弃,改 `is_source_top_dir()` 排除派生目录(`_imgs`/`.cache`/`auto-annotated*`/`reslice*`)单一来源制,故障方向翻转(新源目录自动纳入,误纳仅多扫不漏修);`import fitz` 改惰性(CI 离线可用)。实测:视野 2,421→**3,119**(新可见 698,`data/r58_bug11_coverage.json` 只读测量);dry-run 端到端零异常 + 账目 sha 闭环;**⚠ 实测修正:盲区当前缺图候选=0**(迁出前已恢复),危害定性=流程潜伏风险,非既成损失;499 份/10,439 处积压全在旧视野(常规增量,恢复执行留用户决策,本轮零语料写入)。`tests/test_recover_images_scan.py` +5(含真实语料冒烟),变异 M1 白名单回退→t1+t5 双拦 / M2 去 `_imgs` 排除→t2+t4 双拦;套件 184 passed + 1 xfailed。明细 `log.md` R58 / `bugs.md` BUG-11 |
| 🟢 FIXED(R44) | **BUG-28 batch summary 硬编码 / BUG-29 回填报告硬编码(账目覆盖家族)** | BUG-21 家族延伸:--out 独立批量跑会静默冲掉生产 batch-C 的 summary(R44 修复,`derive_summary_path`,3 回归含集成级+变异验证)/ backfill 回填报告同病(R44 修复,`--report` 选项,真实运行验证生产报告 sha256 前后不变)。教训:硬编码证据工件写路径是跨脚本家族,D-02 治理应并入同一扫描面。明细 `bugs.md` BUG-28/29 |
| 🟡 | **Resolver Identity 消费 v2(BUG-22 最后一层)** | preprocessing 侧身份模型已落地。契约纸面冻结(R48)+ R49 审查通过 + R50 用户裁定进入 Consumer Audit 阶段。**R52:参考 Resolver 已实现** `scripts/resolver_reference.py`(契约逐条落地,import 面零身份推断,CI +12);真实 88 份首跑 ADMITTED 71 / QC_FAIL 16 / V1 1,units 1664,字节确定。**R53 首轮实现级对抗审查通过 + 用户验收(R54 裁决落盘)**:独立重算 88 份/1664 单元 **0 findings**;变异 15/15;**0 结论级翻转、0 新生 resolver 缺陷**。IR 以 `resolver_ir.json@sha256:fbcf41ab…b04a5` 引用;STALE 仅 span 越界信号(用户裁定:边界维持不扩大,semantic stale 归人工/LLM) |
| 🟢 ESTABLISHED(R54) | **F1 Structural Consistency Check(Audit Invariant)** | 用户 R53 裁决实施,定位 **Audit Invariant only**(非 Gate、非 resolver admission rule):QC 裁决对象(切片/annotated 锚点)vs Resolver 抽取对象(manifest spans × 当前源)四项对账(source_version_sha/行号/span hash)。实测:88 份真实语料 **2403/2403 单元 0 漂移**;变异 4/4 咬住 + staged 漂移实证(F1 报 DRIFT 而 Resolver 照常 ADMITTED → 必要性)。**二轮边界攻击 R-ACC-12/13/14**:语义错误 13/13 结构全链绿(Admission 必要性量化)、material 消费零重塑、unresolved 消费不变量 0 findings + 下游默认值攻击面 596 槽位登记。工具 `scripts/audit_f1_consistency.py` + `scripts/r54_round2_attack.py`,CI +11。**审计工具自身缺陷 2 项本轮抓获并修复**(R-ACC-14 检查器 schema 误读 2210 伪 findings;F1 汇编卷锚点匹配) |
| 🟢 ESTABLISHED(R50;R51 对抗审查收口) | **审计治理机制:Audit Snapshot Manifest + Input Integrity Gate** | R49 用户建议转实施:`scripts/audit_integrity.py`——① **Input Integrity Gate**:所有审查工具执行前后**原件集** sha256 对账,漂移即 RuntimeError fail-closed;**作用域限定(R51 A3 实测)**:防御审查/变异代码改动原件(R46 BUG-29 家族),不覆盖 staging 拷贝污染(R49 家族,仍靠控制组保真检查);接线活性经 sabotage 变异注入实证(两工具均咬住)。② **Audit Snapshot Manifest**:确定性快照(无时间戳,字节可复现,顺序无关),报告引用快照摘要而非动态目录;88 份输入面 356 文件 → `data/audit_snapshot_R50_input_baseline.json`(`R50_input_baseline@sha256:795ee1e7…beb`),**R51 独立重算 356/356 逐 sha + 摘要一致、record 重跑字节级全等**。CI +9 测试(`tests/test_audit_integrity.py`)。R51 审查发现:R50 一处过强主张(Gate 防 staging 污染,A3 证伪,已勘误)+ 1 死分支(已删)+ mutation 工件随机 uuid 致不可复现(已归一 `<STAGING>`,两跑字节一致)。套件 **143 passed + 1 xfailed**(本地;CI 126+17 skip) |
| 🟡 | **第三轮外部审查（R29）** | 评级：🟡 有条件通过代码层 / **🔴 不通过全量生产放行**。CI/工程骨架/fixer/QC 契约已证；剩余风险从"代码会不会坏"转移到"**结构合法但语义切错**"（D1 语义错位区间、D2 跨题污染、D3 composite 复杂组合、D4 orphan 链、D5 真实 OCR 噪声、D6 OCR 服务链零测试、D7 真实 MIMO 准确率未自动化证明）。下一轮攻击方向转换：silent-mis-segmentation。方案见 log.md R29（战术 A：对 batch-C 50 份真实产物跑语义代理检测 C13/C14/C15，零 LLM 成本）→ **R30 已执行，确证 BUG-22** |

---

## 数据口径备忘

- 源 md **3120 份**（corpus_scan 口径，含 1 份 `.restored.md` artifact；真源 ~3119）；其中 3113 可配 PDF。
- `auto-annotated-v6` 1434 份 = **旧规则批注**（已弃用，仅供历史对照，非当前口径）。
- `resliced-pilot` 16 份 = 试点,**R36 已迁移 identity v2(15/16;第 16 份被 BUG-24 拒写仍 v1,裁决 v1/v2 一致 FAIL)**,QC 15 PASS / 1 FAIL;`Ocr-markdown\reslice-batch-C` 50 份 = batch-C LLM 重切产物（R31 迁移后 QC 38 PASS / 12 FAIL,12 份 FAIL 均为既有 C3/C5/C6/C7/C9 缺陷,**无 C13**）。
- 页额度 `data\ocr_page_usage.json`：`{date,used}`，每日 20000，午夜重置，API 侧为最终闸门。
