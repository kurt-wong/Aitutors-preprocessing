# 规则登记册(rule_registry.md)

**来源**:用户 R56 二审裁定(2026-09-13)——立即采纳 G-TAX-1(Rule Taxonomy)+ Rule Retirement Policy;
G-RES-1/G-BOUND-1 落 `resolver_contract_design.md` 附录 D;G-SCHEMA-1 延期至 IR vNext;G-AUD-1 暂不实施。

**taxonomy 五类**(新增规则必须归入其一):

| 类 | 含义 |
|---|---|
| FACT_INTEGRITY | 数据事实保真(源字节、hash、锚点、图片/表格不丢) |
| STRUCTURE | 结构合法(标记配对、区间嵌套、span 顺序) |
| IDENTITY | 题号身份(scope、唯一性、printed/canonical 分离) |
| EVIDENCE | 证据与出处(provenance、basis、复核项显式化) |
| QUALITY | 质量测量(OCR 噪声、语义代理)——**测量仪,非 Gate** |

**登记字段**:每条规则必须有 purpose(为什么存在)/ attack surface(防什么,附真实攻击出处)/
evidence(哪轮攻击/实测证明必要)/ retirement(退役条件)。

---

## 1. 生产 QC(reslice_qc.py,Gate 裁决面 C1–C14)

| ID | 类 | purpose / attack surface | evidence | retirement |
|---|---|---|---|---|
| C1 | STRUCTURE | 题干/答案区标记配对完整 | R46 QC 变异 17/17 咬合 | 生产 Gate;退役=切片格式废弃且有替代证明 |
| C2 | IDENTITY | manifest 题号覆盖=源题号集合 | BUG-21 家族;R44 18/4 实测 | 同 C1 |
| C3 | STRUCTURE | 每单元答案区非空 | R44;c09-01 源面答案缺失如实 FAIL | 同 C1 |
| C4 | STRUCTURE | 综合题必含 material/questions | R29 D3 攻击面 | 同 C1 |
| C5 | FACT_INTEGRITY | 源图片行全覆盖进切片(防丢) | BUG-17 家族;c07-01 实测 | 同 C1 |
| C6 | FACT_INTEGRITY | 源表格行全覆盖(卷面须知类豁免) | R44 逐行复证 | 同 C1 |
| C7 | QUALITY | 卷面指令不入库(本大题共X小题/答题卡) | c13-02 版本噪音轮(R55 行级证据) | 同 C1 |
| C8 | FACT_INTEGRITY | annotated 去锚点后与源逐行一致 | R43 锚点方案;R55 零漂移复证 | 同 C1 |
| C9 | STRUCTURE | 试卷结构行不得混入单元区间 | c09-02 实测(R44) | 同 C1 |
| C10 | STRUCTURE | META 锚点 start/end 配对 | R43 | 同 C1 |
| C11 | QUALITY | 详解区不含原题复述 | R18 人工抽审发现 | 同 C1 |
| C12 | STRUCTURE | material ⊆ questions 嵌套不变量 | B1 审查;R54 composite 泄漏 fail-closed | 同 C1 |
| C13 | IDENTITY | 非 keep 持有者间题号身份冲突 | R34 v2 / BUG-23 guard soundness | 同 C1 |
| C14 | IDENTITY | 缺 section 不得静默 PASS(identity_scope_missing 复核项) | BUG-23;R55 覆盖穷举 | 同 C1 |

## 2. 语义探针(semantic_probe.py,**测量仪,不是 QC**)

| ID | 类 | purpose / attack surface | evidence | retirement |
|---|---|---|---|---|
| P13 | QUALITY | 答案虚指:答案区无任何答案形态 | R30 校准;R46 双向变异 8/8;R55 重放全等 | 探针可替换;退役=新探针经同等校准+双向变异 |
| P14 | STRUCTURE(代理) | 跨题污染代理(D2):正文区行首非本单元题号 | 同上 | 同 P13 |
| P15 | IDENTITY(代理) | 答案区归属错位代理(D1);共享答案行跳过 | 同上 | 同 P13 |

探针纪律:报警 ≠ 缺陷(R45/R46/R55 三轮分诊实证);探针结论只以族级账目+逐行留档表述(F-r55-3)。

## 3. F1 结构一致性(audit_f1_consistency.py,**Audit Invariant only**)

| ID | 类 | purpose / attack surface | evidence | retirement |
|---|---|---|---|---|
| F1 四项对账 | FACT_INTEGRITY | QC 裁决对象 vs Resolver 抽取对象(source_version_sha/行号/span hash) | R54:88 份 2403/2403 MATCH;staged 漂移实证必要性 | Resolver 存续期内不退役 |
| I0 | STRUCTURE | IR answers 表对象形状 | R-ACC-14 schema 误读教训(2210 伪 findings) | 同 F1 |
| I1 | STRUCTURE | 答案区间重叠不变量 | R-ACC-14,0 findings | 同 F1 |
| I2 | EVIDENCE | missing 必须入 unresolved(禁静默) | R-ACC-14 | 同 F1 |
| I3 | QUALITY | 哨兵值检测 | R-ACC-14 负向对照 6/6 | 同 F1 |

F1 定位铁律(用户 R53 裁决):**非 Gate、非 resolver admission rule**;对语义错误无检出义务(R-ACC-12 量化)。

## 4. 审计治理机制

| ID | 类 | purpose / attack surface | evidence | retirement |
|---|---|---|---|---|
| Input Integrity Gate | FACT_INTEGRITY | 审查工具执行前后原件集 sha 对账,漂移 fail-closed | R50 建;R51 sabotage 咬合;作用域=原件集(staging 污染另靠控制组) | 永久(治理基础设施) |
| Audit Snapshot Manifest | EVIDENCE | 确定性快照,报告引用摘要而非动态目录 | R50 基线 356 文件;R51 独立重算一致 | 永久 |
| 三边界纪律 | EVIDENCE | Resolver 只做结构/Gate 只证明约束/PENDING_REVIEW 不得为提 PASS 率扩自动规则 | R47 用户裁定 | 永久(架构原则) |

## 5. 攻击面套件(R-ACC-1…14,审查武器非规则)

登记为攻击家族:实现级审查 1–11(R53,15/15 变异)+ 边界攻击 12–14(R54:语义错误 13/13 全链绿、material 零重塑、unresolved 0 findings + 596 槽位登记)。
退役条件:对应契约条款废弃;否则随 Resolver 存续。

## 6. Rule Retirement Policy(登记册运行规则)

1. 新增任何规则/检查/探针/不变量:**必须先在本册登记**(ID、类、purpose、attack surface、evidence、retirement),CI 有覆盖测试钉住(见 `tests/test_rule_registry.py`)。
2. 生产 Gate 规则(C 族)退役:须用户裁定 + 替代证明 + 回归验证,禁止静默删除。
3. 审计轮次脚本(rNN_*/pac_audit_* 等)是**一次性武器 + provenance 证据**:永不退役、永不复用改造;统一审计框架(G-AUD-1)经裁定"暂不实施",自某轮批准后仅对新轮次生效。
4. 测量仪(探针)可替换,但替换须经同等校准与双向变异,并更新本册 evidence。
5. 防递归陷阱:不为审计工具新增审计工具,除非有具名攻击面 + 用户裁定(审计审计系统的默认答案是"不")。
