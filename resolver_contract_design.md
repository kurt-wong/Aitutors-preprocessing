# Resolver 消费契约设计评审稿 (resolver_contract_design.md)

> **状态**:v0.1 纸面稿(R48,2026-09-13)。resolver/compiler/gate/admission 在仓库内 **NOT_BUILT**(`data/pac_track_round1.json` 如实记录)——本稿在实现存在之前冻结**消费契约**,实现后按附录 A 对抗语料开实现级审查。
> **输入裁定**:R47 用户架构级复核(优先序 ① Gate+Resolver Boundary;三边界纪律;ArtifactWriter Contract 候选)+ R42"resolver 必须消费 v2,不得重新发明 identity"+ R36"生产数据不得并存两套 identity contract"。
> **纪律**:每条契约必须挂证据出处;纸面契约不冒充已验证性质——本稿全部条款的验证状态为「纸面冻结,待实现后实测」,唯一例外是 §6 生产侧前置条件(R48 已实测)。

---

## 0. 定位与非目标

- **是什么**:preprocessing(Identity v2 + QC + backfill)与 Question IR 之间的消费契约——resolver 如何读取、拒绝、降级、传递 preprocessing 产物。
- **不是什么**:resolver 内部算法设计、IR schema 设计、入库方案(各自另立设计稿)。
- **核心风险(R47 用户判定)**:入口(Identity 层)已经过多轮对抗加固,但消费层可能**重新解释事实**——resolver 若自行推断身份/语义,V2 时代"程序替用户判断事实"的问题会在下游重生。

## 1. 三边界(R47 用户裁定,强制)

| 层 | 只回答 | 禁止 |
|---|---|---|
| **Resolver** | "能不能定位"(structural only) | 任何语义判断(如 `if answer looks_like_solution: accept()`)、任何身份重推断 |
| **Gate** | "约束能不能被机器证明" | 用启发式放行换取 PASS 率 |
| **Admission** | "人类是否接受不确定性" | 被前两层的静默降级绕过 |

**证据出处**:R47 裁定原文;V2 教训(log.md R1–R15 时代 LLM/程序替用户判断事实);R34"QC 只验证已建立的语义事实,不做语义推理"同源原则。

## 2. 输入契约(C-IN)

| # | 契约 | 证据出处 |
|---|---|---|
| C-IN-1 | **只消费 identity v2**。pipeline 原生输出是 v1,必须经 `phase2_identity_backfill` 回填后才可消费;禁止直接消费 pipeline 原生输出。 | R44 Gate 实测(PAC 22/22 原生 v1 → 回填后 v2);R36"不得并存两套 identity contract" |
| C-IN-2 | **消费 QC verdict,不得以产物存在为消费依据**。`write_outputs` 对 validation_issues 非空仍写产物——产物存在 ≠ 可消费。 | R41 B-04(代码位置证据);BUG-21/28/29 家族(账目覆盖会伪造"存在") |
| C-IN-3 | **裁决三态逐级传播**:FAIL → 拒绝/隔离;PENDING_REVIEW → 强制人工通道,**禁止自动转 PASS**;PASS → 可自动消费。 | R34 三态语义;R35 Evidence Soundness;R47"不得为提高 PASS 比例扩展自动规则" |
| C-IN-4 | **不重新推断身份**。身份键 = `question_numbers`(canonical,全卷语义)+ `section_ref`;`unit_id` 是 display alias,**不可作任何键**(汇编卷大量重复);`printed_number` 是 Source Fact,**永不改写、永不猜测**(unknown > guessed)。 | R32 §1.3/R33 A6(78 单元 unit_id 重复);R34 printed provenance 纪律;R47 printed 硬化方向 |
| C-IN-5 | **basis 语义只读**。`keep` 是个体豁免(resolver 不得因重号自行补 keep、不得因 basis 缺失自行推断豁免);basis 值域校验按 §10.7 schema-validation-only 方向处理(schema violation,不进 FAIL 裁决)。 | R33/R34 划分语义;R42 BUG-27;R47 修订 |
| C-IN-6 | **answer 区编号可与题干区不一致**;答案表键位 = 全卷答案编排编号(canonical answer-key slot),是 canonical_number 最强证据源,**不是答案顺序、不是数据库 identity**。 | c13-02 实测(题干区"共 1 小题" vs 解析区编号 10/11,源卷版本噪音);R19/R32 §4 |
| C-IN-7 | **answer_lines 单行 `<table>` 按题号取对应 td**,切片层保持现状。 | R19 决策(14 份 304 单元实测);status.md 入库前置任务 |
| C-IN-8 | **锚定用行号,不用标题形态**。OCR 对答案行的标题化是随机的(c06-02 fresh−baseline=12 处、c10-02=6 处),resolver 定位必须以 manifest 行号区间为准,不得重新解析标题层级。 | R44/R46 OCR 漂移量化 |

## 3. 失败传播契约(C-FAIL)

| # | 契约 | 证据出处 |
|---|---|---|
| C-FAIL-1 | FAIL / PENDING_REVIEW / MISSING / STALE 任何一态**不得被 resolver 或其下游静默转换为 PASS**;每级转换必须留痕。 | R41 Gate 攻击面 B(用户标记为最危险系统级攻击面);BUG-26(recompile 洗 v2 身份头 → QC 静默降级 v1 语义,已修) |
| C-FAIL-2 | QC verdict 为 FAIL 的文件若仍被人工放行进 IR,必须走 Admission 层显式记录,不得在 resolver 内消化。 | R41 B-03 优先级语义(FAIL 压过 PENDING_REVIEW);三边界 |
| C-FAIL-3 | resolver 运行时发现输入非 v2 / verdict 缺失 / 工件漂移,应 **fail-closed 拒绝该文件**,不得降级重算替代(重算即重新解释事实)。 | BUG-24 拒写先例(fail-closed 如实拒绝优于错误写入);C-IN-1/2 |

## 4. 输出工件契约(C-OUT,ArtifactWriter 候选首批条款)

| # | 契约 | 证据出处 |
|---|---|---|
| C-OUT-1 | resolver 产出(IR、报告、日志)路径必须**派生自 --out 类参数**,禁止写死覆盖既有证据工件。 | BUG-21/28/29 家族;R47 ArtifactWriter Contract 建议 |
| C-OUT-2 | 每单元 IR 必须携带 provenance:源文件、源行号区间、QC verdict、identity 字段原样(禁止在 IR 中重塑 printed/canonical)。 | C-OUT 目标"产物正确但无法证明为什么正确"(R41 攻击面 C);review_protocol 规则 2 |
| C-OUT-3 | resolver 自身报告中恢复/成功类声明按 review_protocol **规则 4** 报 numerator/denominator/proof method。 | R46 c09-01 事件(23/34);R47 规则化 |

## 5. 已知消费风险登记(实测数字,规则 4 口径)

以下为 resolver 实现时**必须显式处理、不得假装不存在**的真实数据形态:

1. **printed 未回收是常态**:batch-C 回填 printed provenance = source_line 948 / migration_report 134 / **unknown 402(27.1%,printed 全部为 null)**;PAC c01-02 括号式题号 28/28 unverified、c09-01 23/34 recovered(11 单元 printed=None)。→ IR 不得回填猜测值。
2. **源面答案缺失**:c09-01 6 题 C3(源卷就没有答案)、历史卷(2021 四十三中)4 题答案缺失——忠实反映,不是流水线缺陷。→ IR 缺答案是合法终态。
3. **答案/解析不分离**:c12-02 Q24 answer 区为【解析】散文(答案内容在解析内)——绑定语义正确,分离质量项由 resolver 裁定,**不得静默重绑**。R30 另两例:政治 U35 源文档同行合并致 material 首行边界污染 1 行;地理 U13-14 答案区"4. A"实为"14."OCR 丢字(resolver 按题号取数会漏 Q14)。
4. **OCR 行融合**:c11-02 L137 三重融合(标题+正文同行)被 SectionLocator 如实收为 section start(ACCEPTED OCR LIMITATION 家族)。
5. **PENDING_REVIEW 是设计产物不是噪音**:keep 证据语义充分性机器不可证(R35 诚实边界),人工通道是契约的一部分。

## 6. 生产侧前置条件预检(R48 实测:`scripts/resolver_contract_preflight.py`)

对生产 66 份(batch-C 50 + pilot 16)+ PAC 22 份共 88 份产物逐份机器检查十条前置(pc1 v2 在册 / pc2 identity 无 fail / pc3 无 pending / pc4 QC verdict 可计算 / pc5 basis 值域 / pc6 provenance 值域 / pc7 provenance 与 printed 反伪造一致性 / pc8 section_ref 可解析 / pc9 行号区间界内 / pc10 源文件在位)。结果见 `data/resolver_contract_preflight.json` 与 §6.1。

### 6.1 实测结果(R48,`data/resolver_contract_preflight.json`)

- **88 份(batch-C 50 + pilot 16 + PAC 22)逐份机器检查:87/88 零 findings**;
- 唯一 finding = **pc1 ×1**:三十一中化学(pilot)仍为 v1——known(keep 三方裁决挂起件,fail-closed 拒回填),**恰证明 pc1 拒收路径有真实命中**,不是空检查;
- pc2–pc10 全部 0:identity 无 fail、无 pending、QC verdict 87/87 可计算(v1 件按契约不进入 QC 消费路径)、basis/provenance 值域与反伪造一致性、section_ref 零悬空、行号零越界、源文件全部在位;
- QC verdict 分布与台账算术闭合:**PASS 71**(batch-C 38 + pilot 15 + PAC 18)/**FAIL 16**(batch-C 12 + PAC 4);
- 结论(限定口径):**在当前 88 份产物上,生产侧满足 resolver 输入契约的机器可检前置条件;此为 producer-side 事实,不构成 resolver 实现正确性的任何证明**(消费侧证据须待实现后按 §7/附录 A 开审)。

## 7. 未来实现的验收标准(R-ACC,实现审查逐条测)

1. **R-ACC-1**:resolver 拒绝 v1 输入(fail-closed),拒绝理由可机器读取;
2. **R-ACC-2**:FAIL 文件不进自动消费路径;PENDING_REVIEW 文件不自动转 PASS(变异验证:放宽即测试红);
3. **R-ACC-3**:resolver 输出 IR 的 printed/canonical 与 manifest 逐单元 byte-equal(不得重塑);
4. **R-ACC-4**:resolver 不导入 `question_identity` 之外的身份推断逻辑——身份唯一来源 = manifest v2 字段(实现审查做 import 面与代码路径审计);
5. **R-ACC-5**:c13-02 形态(answer 区编号不一致)不崩溃、不静默错配,处置留痕;
6. **R-ACC-6**:R19 答案表 td 切分正确(14 份 304 单元语料);
7. **R-ACC-7**:输出工件遵守 C-OUT-1(变异验证:写死路径即测试红,BUG-28/29 教训,且此类变异必须先备份目标工件——R46 补记);
8. **R-ACC-8**:附录 A 对抗语料全量跑通,每样本处置可解释(与 PAC 同纪律:FAIL 必须非静默、可归因)。

### 7.1 R49 审查补充:覆盖矩阵闭合

R49 纸面审查发现 v0.1 的 C 条款→R-ACC 映射存在缺口(C-IN-5 / C-IN-8 / C-OUT-2 / C-FAIL-1 的 MISSING·STALE 两态无验收条款),补:

9. **R-ACC-9(C-IN-5)**:resolver 不得根据重号形态自行补 keep/豁免——构造跨节重号输入,断言 resolver 输出保持原 basis 且按 C-FAIL-3 fail-closed;
10. **R-ACC-10(C-IN-8)**:同内容不同标题形态(答案行标题化随机漂移,c06-02/c10-02 实测形态)输入,断言 resolver 定位结果按行号区间不变——禁止重新解析标题层级;
11. **R-ACC-11(C-OUT-2 / C-FAIL-1 补全)**:IR 逐单元携带 provenance(源文件/行号区间/verdict/identity 原样);MISSING(工件缺失)与 STALE(manifest 与源漂移)两态进入与 FAIL 同级的拒绝通道,不得静默降级。

## 附录 A · 对抗语料登记(ready-to-fire)

| 语料 | 量 | 攻击目标 |
|---|---|---|
| PAC 第一轮产物 | 22 份(18 PASS / 4 FAIL) | 真实 OCR 漂移输入;4 份 FAIL 的 C-FAIL-2 处置;c09-01 printed/canonical 分离;c13-02 版本噪音;c12-02 答案在解析内;c01-02 括号式题号;c11-02 融合 |
| batch-C | 50 份(38 PASS / 12 FAIL) | keep 93 单元豁免消费;unknown 402 单元;汇编卷 unit_id 重复;R19 答案表 td |
| pilot | 16 份(15 PASS / 1 v1 FAIL) | v1 拒收路径(三十一中化学);BUG-22 原形态卷(Q26-34) |
| R30 语义探针校准卷 | 政治 U35 / 地理 U13-14 等 | material 边界污染、答案区 OCR 丢字取数 |

**开审条件**:resolver 实现存在且 R-ACC 清单有对应测试骨架;开审纪律同 PAC(R46 级对抗:独立重算 + 变异 + 穷举,不得抽样冒充全称)。

## 附录 B · R50 用户裁决补记(2026-09-13)

1. **阶段裁决**:PAC + Identity 阶段 🟢 冻结(R49 为该阶段最后一类高价值攻击——审查体系自身可信度);**下一阶段正式启动 Resolver Consumer Adversarial Audit**。审查目标不是"resolver 能不能跑",而是 **resolver 是否会重新解释已冻结的事实层、重新制造 V2 式隐性错误**。用户指定攻击清单:① section 丢失 ② basis 被重新解释 ③ provenance 丢失 ④ composite material 合并错误 ⑤ single question material 丢失 ⑥ shared material duplication。
2. **provenance 一等公民(R50 用户方向,C-OUT-2 实施基准)**:IR provenance 不得埋在 metadata 里,应接近结构化对象 `EvidenceProvenance(source_version, source_line, extraction_method, confidence_state)`;否则后续追责困难。Resolver 实现轮按此形态细化 schema。
3. **输入基线冻结(BUG-30 类 Audit Snapshot Drift 治理)**:本阶段 88 份输入面(batch-C 50 + pilot 16 + PAC 22 的切片/manifest/annotated/源 + preflight + 三份 QC 工件,共 356 文件)已快照为 `data/audit_snapshot_R50_input_baseline.json`,引用口径 **`R50_input_baseline@sha256:795ee1e7663424c1245e651d2139573d3bd2322f06662cc677bc0e7e3bc89beb`**。Resolver 审查轮的输入以此为准;数字声明引用快照摘要,不再引用动态目录。
4. **审计工具纪律(R50 机制化,R51 作用域实测限定)**:所有审查工具必须过 **Input Integrity Gate**(`scripts/audit_integrity.py`:执行前后**原件集** sha256 对账,漂移即 fail-closed)。**作用域(R51 A3 实测)**:Gate 防御"审查/变异代码改动原件"(R46 BUG-29 家族),**不覆盖 staging 拷贝污染**(R49 自我覆盖家族)——拷贝保真由控制组检查负责,两道防线缺一不可。R49 两个审计工具已接线(接线活性经 sabotage 变异注入实证)。
5. **printed 硬化(优先序④)批准方向不变**:unknown > wrong certainty,宁可 `printed_number=null` 不写猜测值。

---

## 附录 C · R54:F1 Audit Invariant 落地 + Resolver 审查第二轮(2026-09-13,用户 R53 裁决)

### C.1 用户裁决(R53 验收)

1. **R53 第一轮验收通过 🟢**;定性纪律:"没有证明 Resolver 正确,而是证明 Resolver 按冻结契约实现时,没有发现违反契约的行为"。Reference Resolver 继续保持审查对象,**不进入生产链路**。
2. **F1:实施,定位 Audit Invariant only**——不是 Resolver admission rule、不升硬 Gate(不得让 Resolver 变成第二套 QC);检查面严格四项:**source_version_sha / start_line / end_line / span hash**;不检查语义正确性/题目完整性/答案合理性(属 QC/Admission)。
3. **STALE 边界维持不扩大**:Structural stale(Resolver 可检)/ Source stale(provenance 检)/ Semantic stale(人工/LLM 审)三分类;Resolver 只负责第一类。
4. 第二轮攻击面:**R-ACC-12** QC→Resolver 边界(契约合法但语义错误)/ **R-ACC-13** Material Consumer / **R-ACC-14** unresolved 消费。

### C.2 F1 Structural Consistency Check(`scripts/audit_f1_consistency.py`)

三方对象:resolver 侧 = manifest spans 应用于当前源(strip_meta 行切片);QC 侧 = annotated.md META 锚点区间(行号锚定 + 编译时刻文本留档)+ 切片 md 区文本(题干区/答案区/详解区)。期望值独立重实现(不 import 生产 compile);共享答案表区内容不可比 → 行号注释逐字比对 + 如实标 UNCOMPARABLE。可选 `--ir` 与 Resolver 运行时刻 provenance(source_version/source_lines)三方对账。输出确定性(无时间戳),过 Input Integrity Gate。

**实测(R54)**:88 份真实语料(R50 冻结基线)控制组 **88/88 文件、2403/2403 单元全 MATCH、0 漂移**;294 个 shared-answer 区如实 UNCOMPARABLE。工件:`data/r54_f1/f1_summary.json`(入库)+ `f1_report.json`(4.8MB 逐单元明细,sha256 见 summary 内 `full_report` 字段,不入库——R52 先例,可从冻结基线字节级复现)。灵敏度:代码变异 4/4 被 CI 咬住(状态硬编码 MATCH / slice 检查失效 / 消费不变量检查器失效 / Gate sabotage 接线活性)+ 真实语料 staged manifest 漂移(改 manifest 不重编译)→ **F1 报 DRIFT,而 Resolver 同一态照常 ADMITTED**——F1 存在必要性的直接实证;控制组零变异 staging 复现原件 MATCH。

### C.3 第二轮实测结果(`data/r54_round2_attack.json`)

- **R-ACC-12**:变异后重编译全部工件(生产可 representable),整链 QC×Resolver×F1 测量。**stem 尾行丢弃 6/6、answer 错绑下一单元 6/6 全链绿**(QC PASS + ADMITTED + F1 MATCH)——结构链全绿而语义已错,**量化坐实语义正确性只能由 Admission/人工层承接**;answer 错绑 6/6 未产生 answer_number_mismatch flag(错绑目标首行无题号前缀,flag 是结构观察不是保证,如实记录)。options 尾行丢弃 1/1 全链绿(样本内仅 1 个合格单元);material 外扩族样本无合格单元(denominator 0,如实)。
- **R-ACC-13**:material 顺序交换 / shared 错绑定 / single 丢失三族,resolver 输出与独立重算期望(不 import resolver)**consumers 精确相等、文本单份无复制、零重塑**;composite 泄漏(material 越过 questions 相交不嵌套)被生产 C12 咬住 → REJECTED_QC_FAIL fail-closed。控制组复现原件。
- **R-ACC-14**:真实 IR(528 表单元)消费不变量 I0–I3 **0 findings**;口径对账:26 键位单元/30 答案键、502 全 unresolved 单元/**596 unresolved 槽位**(与 R53 单元级口径互洽);负向对照 6/6 咬住(overlap/missing/sentinel×2/shape/干净)。**下游默认值攻击面量化:`answers.get(q, "")` 类朴素消费会把 596 个 unresolved 槽位静默变成"已解为空"**——未来 Agent/UI 层消费契约必须显式处理 unresolved(登记为 C-OUT 消费侧条款候选)。
- **审计工具自身缺陷(本轮抓获并修复,如实入册)**:R-ACC-14 检查器首版按错误数据形状编码(IR 的 `answers` 是 `{cells, method, answers, unresolved}` 表对象,非逐题映射),真实 IR 上产生 2210 条伪 findings——"检测器必须先被真实数据校准"(R30 教训同族)再次实证;已按真实 schema 重写 + I0 形状检查 + t11 防回归。另 F1 匹配逻辑一处缺陷(无 span 单元误消费同题号键下他单元锚点,汇编卷触发)由 88 份控制组抓获并修复(修复后 2403/2403)。

### C.4 边界(如实)

- F1 只证明**结构一致性**;R-ACC-12 恰证明它对语义错误**无检出义务、也不应有**(Audit invariant,非 Gate)。语义正确性仍属 QC 语义探针(测量仪)/Admission 人工通道。
- R-ACC-12/13 攻击样本 = PAC 单文件 + 单个 material 富样本各 1 份,K=6/族枚举(manifest 序前 K 个合格单元,非按结果挑选);结论限定该样本域,不外推全语料发生率。
- E1 staged 漂移演示中 resolver 行为(ADMITTED)符合契约:Resolver 消费 QC verdict,该态下 QC 仍 PASS(其裁决对象是切片)——F1 正是为暴露该跨组件缝隙而存在,且按裁决不改变 admission 语义。

## 附录 D · R56 二审裁定 + R57 治理落地(2026-09-13,用户裁定)

### D.1 裁定记录

1. **R55 收口通过 ✅**(R45 声明对抗性复证:顶层声明全成立;F-r55-2/3/4 入册)。
2. **立即采纳**:G-TAX-1 Rule Taxonomy + Rule Retirement Policy(落地 `governance/rule_registry.md`,CI 钉住)、G-RES-1(本附录 D.2)、G-BOUND-1(本附录 D.3)。
3. **登记但延期**:G-SCHEMA-1 basis 拆分(`identity_policy`+`evidence`)→ **IR vNext / Admission vNext 落点,不反向修改 Identity v2**(v2 经 R34/35/38/40/42/49/53 多轮验证,现改会重开 migration/resolver/admission 风险)。
4. **暂不实施**:G-AUD-1 统一审计框架——历史 audit artifact 具 provenance 价值,不重构;若未来批准,仅对新轮次生效(登记册 §6.3)。
5. 阶段路线(用户认可):Identity v2 冻结 → **BUG-11/14/15 数据卫生(序:11→14→15)** → basis schema-only 治理(排期③)→ Admission Layer 稳定化 → V3 Backend 消费。

### D.2 Resolver 禁能力膨胀条款(G-RES-1,显式禁令)

Resolver 的职责边界 = **structural extraction + provenance attach**,以下能力**明令禁止进入 Resolver**(无论需求方理由):

1. **semantic inference**(任何语义真值推断,含"这题切对了吗");
2. **similarity judgment**(同题/相似题判定——归属未来 Question Similarity 层);
3. **knowledge classification**(知识点/难度/题型分类);
4. **answer correctness judgment**(答案正确性判定——归属 Admission/人工)。

违禁判定标准:任何让 Resolver 输出超出"结构事实 + 出处"字段的需求,一律拒绝并登记;正确回应是路由到后续层,而不是就地扩展。此禁令与三边界纪律(R47)同效力,修改须用户裁定。

### D.3 阶段定位原则(G-BOUND-1)

**preprocessing = V3 的 Data Admission Layer,不是"题目解析脚本"**。已由本层证明的事实(OCR 判读、section 归属、identity、结构完整性),V3 Backend **不得重复判断**——重复判断即边界污染(V2 失败路线重演)。Backend 消费面 = 验证过的 IR + provenance + unresolved 显式通道(596 槽位,禁止 `answers.get(q, "")` 类静默默认)。

### D.4 审计惯性防线

用户裁定采纳"审计惯性"预警:规则增长须以登记册为闸口(新增必登记、退役须裁定),**默认拒绝"为审计工具新增审计工具"**(登记册 §6.5)。复杂度倒挂(审计 ≈ 生产链 5.4×,R56 实测)定性为维护成本风险而非正确性风险,治理手段 = 冻结增长 + 分类学 + 退役政策,而非削减已证明必要的检查。
