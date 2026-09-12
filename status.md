# 项目状态 (status.md)

> **规格基准见 `prd.md`**（背景/结构/数据契约/实现逻辑以 PRD 为准）。本文件只记录**进度快照**。
> 更新：2026-09-13 · 负责人：Kurt

---

## 一句话现状

**重切路线已成立（试点 16/16 全签核），全量推广尚未启动。** 生产化就绪度 ≈ 原型验证 100% / 生产化 30%。
下一步的门槛不在"能不能切"，而在"源修复收尾 + 全量 runner + 运维闭环"。

---

## 当前阶段

**阶段：LLM 重切 · 试点完成 → 全量推广前准备**（旧的"规则批注 + BERT 训练"路线已于 2026-09-09 废弃，见 PRD §12 决策记录）。

---

## 已完成里程碑

- ✅ **方案定型**：锚点式批注（源不动、只插锚点、LLM 只输出行号）；根本规则 R1–R12 逐条确认（PRD §5）。
- ✅ **重切流水线** `reslice_pipeline.py`（v2.1 嵌套格式）：行号化→mimo-x-pro-preview→确定性校验→三产出，支持 `--resume`/`--recompile`。
- ✅ **试点 16/16 通过**：九大学科 × 三学段，用户全部签核；`reslice_qc.py` C1–C10 全绿（`data/reslice_pilot_qc.json`：16 PASS / 0 FAIL）。对比 v6 全量基线合格率 4.0%，路线成立。
- ✅ **全库源缺陷量化** `corpus_scan.py`（3120 份）：双重识别 138 份/148 处；裸 LaTeX 954 份（简单 4918 / 复杂 610）。
- ✅ **配图恢复** `recover_images.py`：43,463 张（0.64 GB），原始 md 与 v6 悬空引用已修复（目录覆盖待扩，见 PRD §10-C）。
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
| 🟢 | **BUG-24 分节标题过滤器误杀(R36 发现 / R37 修复)** | `_heading_rows` 的 `答案\|解析\|评分` 排除器整行子串匹配,误杀含 note 的真实分节标题(三十一中化学 L324 填空题节)→ SectionLocator 假阴性。用户裁定:应修、现在修、只修 SectionLocator 不动 Identity/keep。R37 修复:排除器两阶段结构角色识别(结构归一化 + 归一头部窗口 10 判 marker),**全链复验见下 R37 行**。残留:三十一中化学 FAIL 理由已变为正确的"跨分节重号含多个非 keep",**keep 三方裁决仍是独立决策点**;`## 解析几何` 类 topic 词假阴性全语料 1 例(诚实边界) |
| 🟢 | **BUG-24 修复全链复验(R37)** | 改码前先锁影响面:before 快照(bug24_locator_snapshot)+ before QC 与 R34 提交基线逐文件零差异;全语料盘点 3120 卷:恢复 848 行、**0 答案内容行误升**,reslice-scope 恢复 13 行逐条人检(6 真分节 + 7 benign 源结构标题)。修复后:**11 份 manifest 重生成**(batch-C 7 + pilot 4,三十一中如实拒写故字节不变),**QC 裁决集零翻转**(38/12、15/1),fails 全部 0→0,字节级幂等 66/66,NEW-OLD diff `data/bug24_fix_report.json`;验收 `tests/test_bug24_section_locator.py` 13/13(B24-01~08 + 三类变异 sanity);套件 **103 passed + 1 xfailed** |
| 🟡 | **Resolver Identity 消费 v2(BUG-22 最后一层)** | preprocessing 侧身份模型已落地(QuestionIdentity v2 + SectionLocator + basis/basis_evidence + 三态裁决);resolver/IR 层消费 v2 模型属下游设计,随 resolver 项目推进 |
| 🟡 | **第三轮外部审查（R29）** | 评级：🟡 有条件通过代码层 / **🔴 不通过全量生产放行**。CI/工程骨架/fixer/QC 契约已证；剩余风险从"代码会不会坏"转移到"**结构合法但语义切错**"（D1 语义错位区间、D2 跨题污染、D3 composite 复杂组合、D4 orphan 链、D5 真实 OCR 噪声、D6 OCR 服务链零测试、D7 真实 MIMO 准确率未自动化证明）。下一轮攻击方向转换：silent-mis-segmentation。方案见 log.md R29（战术 A：对 batch-C 50 份真实产物跑语义代理检测 C13/C14/C15，零 LLM 成本）→ **R30 已执行，确证 BUG-22** |

---

## 数据口径备忘

- 源 md **3120 份**（corpus_scan 口径，含 1 份 `.restored.md` artifact；真源 ~3119）；其中 3113 可配 PDF。
- `auto-annotated-v6` 1434 份 = **旧规则批注**（已弃用，仅供历史对照，非当前口径）。
- `resliced-pilot` 16 份 = 试点,**R36 已迁移 identity v2(15/16;第 16 份被 BUG-24 拒写仍 v1,裁决 v1/v2 一致 FAIL)**,QC 15 PASS / 1 FAIL;`Ocr-markdown\reslice-batch-C` 50 份 = batch-C LLM 重切产物（R31 迁移后 QC 38 PASS / 12 FAIL,12 份 FAIL 均为既有 C3/C5/C6/C7/C9 缺陷,**无 C13**）。
- 页额度 `data\ocr_page_usage.json`：`{date,used}`，每日 20000，午夜重置，API 侧为最终闸门。
