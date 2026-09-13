# R67 设计报告:Manifest 审计级引导(bootstrap)+ daemon「跑飞」归因

日期:2026-09-13 | 状态:**用户已裁决五项冻结(见 §十),进入 implement;apply 仍须 dry-run diff 人工批准**

---

## ⭐ §十 用户裁决(2026-09-13,冻结,凌驾本报告任何早期草案)

| 决策点 | 裁决 |
|---|---|
| ① pages 未知 | **nullable**(`pages: null` + `provenance`);禁 `-1` 哨兵(污染数值语义)、禁假 `0`(伪事实) |
| ② 时间字段 | **recorded_at 语义**(系统何时知道),绝不冒充 processed_at(OCR 何时发生);bootstrap 条目 `processed_at: null`。勘误:R66 既有 `written_at` 的取值时机本就是"记录写入时刻",故 bootstrap 条目 `written_at` = bootstrap 执行时刻语义自洽,另加显式 `processed_at: null` |
| ③ 625 首扫候选 | **不接受直接重跑**;先 OCR 日志考古 → A 类(日志+路径唯一)入 bootstrap / B 类(弱证据)PENDING_REVIEW / C 类(无证据)不入 manifest;最大化利用既有 provenance |
| ④ apply 时机 | **暂缓**:implement → CI → mutation → dry-run → manifest diff → 人工批准 → apply;diff 必须逐条列 evidence 来源与 confidence |
| ⑤ 覆盖禁令 | **bootstrap 不得覆盖/修改任何已有 manifest 条目**(append-only history;只能为 missing source_rel 补新记录;已有条目原样保留) |
| 原则 | **manifest 是事实账本,不是推测账本**;"看起来处理过"(文件存在)永不入账;最大风险 = 为修历史状态引入新伪事实 |

其他裁决:R66.1 **PASS 收口**;daemon 归因"卡死"正确,worker 生命周期管理(heartbeat/progress checkpoint/stuck detection)登记为未来治理项,不混入本轮;下一阶段顺序 = implement → dry-run → diff 审查 → apply → daemon 新状态确认 → D5-B。

---

## 一、「daemon 跑飞」归因——它没有跑飞,是卡死;真正的风险是前瞻性的

先纠正定性(证据在 R66.1 §1):旧 daemon **不是失控狂跑,而是中途卡死**——
runner(33036)日志冻结于 09-10 21:27:45(扫描至 75/12703),进程存活 2.7 天零输出;
看门狗(38160)每 60s poll 一次却因 BUG-12 家族的监控粒度察觉不到卡死。
「跑飞」描述的是**如果直接重启会发生什么**,其成因分三层:

1. **清单引导缺口(R66 引入机制的固有边界)**:R-OHM-1 只保护「记账之后」。
   manifest 从零开始,任何历史上已处理但输出被搬走的 source 在首扫时
   无记录可查 → NO_MANIFEST_ENTRY → 真实 OCR。这不是代码缺陷,
   是冷启动语义,必须用引导(bootstrap)或接受重跑来填。
2. **历史搬移存量(R64 实锤的跑步机遗产)**:reclassify 搬移输出击败 exists-check。
   R66.1 预检:12,703 PDF 中 10,282 首扫待 OCR;同名 stem 拆分出 625 份
   「历史已处理候选」。但本轮设计探针(见 §三)证明:**625 中仅 1 份有审计级证明**,
   其余绝大多数是跨源同名巧合(stem = 弱身份,用户已明令 Level 3/4 禁 basename 归并)。
3. **从未处理的正常存量(非故障)**:9,657 份 / 19.7 GB 是 daemon 本职待办,
   受 20,000 页/日配额闸门约束,属设计内业务,不是「跑飞」。

结论:不存在需要修的「失控机制」;存在一个需要**治理决策**的冷启动语义。

---

## 二、R67 目标与边界(冻结,待用户批准后才实施)

**目标**:在生产 daemon 激活与 D5-B 之前,把 R63 reclassify 审计日志中
**日志级可证的「source → 已处理输出」**回填进 manifest,使这些 source
在 D5-B 再次搬移输出时被 MANIFEST_DONE 拦截(跑步机切断对历史存量生效)。

**明确不做什么(硬边界)**:
- 不为 625 首扫候选中无审计证明的 624 份做任何「大概处理过」的推断回填
  (禁猜测、禁 stem 级身份、禁 fallback);它们首扫重跑或逐份上报,由用户裁定。
- 不动语义去重 / canonical identity / BUG-14-CHAIN(D5 协议冻结)。
- 不改 runner(回填工具是独立离线脚本,runner 对 manifest 只读消费)。

---

## 三、证据探针(只读实测,2026-09-13,`scripts/_r67_design_probe.py`)

| 事实 | 数值 | 含义 |
|---|---|---|
| 审计记录总数 | 698 | R63 reclassify --apply 的 from→to 全量 |
| from == 唯一 PDF 的 runner 期望输出 | **698/698** | source↔输出映射日志级证明完整 |
| 多 PDF 共享同一期望输出(歧义) | **0** | 无歧义,无需仲裁 |
| to 文件仍在位 | **698/698** | 搬移结果未被后续破坏 |
| 625 首扫候选中期望输出 ∈ 审计 from 集 | **625/625(⚠ F-r67-1 更正)** | 审计证据**全覆盖**首扫受害者 |

**⚠ F-r67-1(当轮自查更正)**:本节首版误写"625 中仅 1 份有审计证明"——根因是探针
`hit += 1; break` 在首个命中即退出(把 ≥1 截断成 1)。修正探针后复证 **625/625**;
dry-run 实测与此一致(624 受害者全部经审计入账,B_pending=0;差 1 份系工具 md 索引
按口径排除 reslice 试验目录,其 source 作为审计源仍入账)。**结论反转后的设计含义:
审计回填同时保护首扫(624 份不再重 OCR,首扫规模 10,282 → ~9,658)与 D5-B 搬移**。
教训(与 F-r65-2 同族):审计武器的统计循环里禁止 early-break,计数必须穷举。

---

## 四、机制设计

### 4.1 工具形态
`scripts/r67_manifest_bootstrap.py`:离线、只读语料、默认 dry-run,`--apply` 显式落盘。
输入:`data/reclassify_audit.jsonl`(698 条)+ PDF 树 + 输出树 + 目标 manifest。
输出:`data/r67_bootstrap_report.json`(确定性:逐条决策 + 汇总计数)。

### 4.2 匹配规则(唯一允许的证据形态)
对每条审计 {from, to}:
1. `from_rel = relpath(from, OUTPUT_ROOT)`(正斜杠归一,F-r64-1);
2. 对全部 PDF 计算 runner 期望输出(`extract_grade_subject` + `sanitize_stem`,
   与 runner 字节级同规则),要求 **from_rel 恰好命中 1 份 PDF**;
3. `to` 必须在位且 >100B;
4. 命中数 ≠ 1、或 to 缺失/过小 → **该条不回填,显式计入 report 的 excluded 桶**
   (fail-closed:宁可少回填暴露重跑,不可错回填吞掉新 OCR)。
等值判定只用完整路径,不用 stem(探针已证 0 歧义,匹配面不放宽)。

### 4.3 清单条目 schema(兼容 validate_entry,新增键仅作留证)
```json
{"source_rel": "...", "source_size": <当前 PDF 字节数>, "source_sha256": "<当前 PDF sha>",
 "output_rel": "<审计 to 相对 OUTPUT_ROOT>", "written_at": "<bootstrap 执行时间>",
 "pages": 0,
 "provenance": "r63-audit-bootstrap",
 "processed_at": "unknown(r63 audit 无时间戳)",
 "audit_from_rel": "<审计 from 相对 OUTPUT_ROOT>"}
```
披露与代价(不掩饰):
- `source_sha256` = **当前** PDF 哈希。OCR 当时的 PDF 状态不可回溯验证;
  PDF 语料惯例不可变,若某 PDF 在 OCR 后被改过,该条会错误抑制重跑——
  以 `provenance` 字段使此类条目永远可审计、可逐条删除(删条=显式授权重跑)。
- `pages: 0` 非事实主张「0 页」,而是「页数未知」;`processed_at: unknown` 同步钉死。
  (若用户认为 0 有歧义,备选:回填时以 `pages: -1` 之类哨兵——但会破坏 validate_entry
  的 int 语义检查?不会,-1 是 int;**此项列为用户决策点 §七 ①**。)
- `written_at` = bootstrap 执行时刻(这是「记录写入时间」的字面事实);
  OCR 时刻由 `processed_at: unknown` 显式承认不可知。

### 4.4 fail-closed 点(逐个可测)
1. 审计文件缺失/坏行 → 显式中止(禁部分静默);
2. 匹配歧义/失败 → excluded + 计数(非静默);
3. 目标 manifest 已存在且含坏行 → 中止(load_manifest 原生 fail-closed 复用);
4. 写入前逐条 validate_entry;写入 append-only + fsync(复用 output_manifest.append_entry);
5. **幂等**:apply 前 load 现有 manifest,source_rel 已在册 → 跳过(不重复追加);
   二次 apply 报告 appended=0。

### 4.5 与生产激活的顺序契约
```
R67 实施(登记→工具→测试→变异→CI)
  → 用户批准 apply → bootstrap 落账(698 条候选,实际以探针口径 698 全匹配)
  → 生产 daemon 重启(A 项验收:进程归属 + manifest 非空载入日志)
  → 首扫观察(625 候选重跑如实入账,配额闸门 20k/日)
  → D5-B reclassify(搬移被 MANIFEST_DONE 拦截 = 跑步机对历史存量生效)
```

---

## 五、测试计划(实施时最低覆盖,全部真实执行)

1. dry-run 零写入(manifest 字节不变、无文件创建);
2. apply 产出 N 条,`load_manifest` 全部合法载入、键归一;
3. 幂等:二次 apply appended=0,manifest 字节不变;
4. 歧义夹具(两 PDF 共享期望输出)→ excluded + 计数,不回填;
5. to 缺失夹具 → excluded;
6. 已有坏行 manifest → 中止(非静默);
7. 条目 schema 钉(必键 + provenance/processed_at/audit_from_rel 在场);
8. 集成钉:回填后对同一 source 跑真实 `decide_skip`(期望输出搬移态)→ MANIFEST_DONE;
9. 真实审计冒烟(698/698 匹配数与探针一致——重放探针结论)。

## 六、变异计划(实施时,字节级还原)

- M1 匹配规则放宽到 stem 级 → 歧义钉必须咬;
- M2 excluded 改静默丢弃 → 计数钉必须咬;
- M3 幂等检查拆除(重复追加)→ 幂等钉必须咬;
- M4 source_sha 写常量/空 → schema/集成钉必须咬;
- M5 写入前校验拆除 → 坏条目钉必须咬。

## 七、待用户裁决的设计决策点

① `pages` 未知的表达:`0 + processed_at unknown`(推荐,兼容现约)vs `-1` 哨兵;
② `written_at` 语义采用「记录写入时刻」+ `processed_at: unknown`(如上)是否接受;
③ **625 首扫候选的处置**:接受首扫重跑(配额闸门内,污染留 D5-E)vs 我逐份输出清单
   供您人工裁定 vs 暂停激活先做更深入的处理史考古(如 OCR 日志逐行匹配,R65 已证
   日志可直接证明部分重复处理——可扩展探针把 625 中能被 OCR 日志证明的子集捞出来);
④ bootstrap 实施工具的 apply 时机:实施+CI 后单独由您授权(推荐)vs 与实施同轮。

## 八、边界

- 本报告零实施、零生产写入;探针只读。
- 698/698 匹配是**审计文件当下与语料当下**的对账;若在 apply 前语料变动,须重跑探针。
- 回填只解决「已证明处理过」的历史存量;它不声称、也不实现输出可用性(语义边界见
  R66 裁定:manifest = processing history,非 availability index)。
