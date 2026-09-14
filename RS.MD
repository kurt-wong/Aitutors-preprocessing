# 会话重启提示词(Resume Prompt)

> 用法:在新会话开始时,让 agent 完整阅读本文件,然后阅读 `log.md`(追加式轮次台账,读最后 3~5 轮)与 `status.md`,即可恢复工作状态。本文件描述截至 **R54** 的状态(main = R54 提交,sha 见 git log;R53 = `d18307e`)。

---

## 0. 项目一句话

LLM 驱动的北京高中考试 OCR Markdown 重切分流水线:把 OCR 产物转换为可入库的题目单元。**试点 16 份已通过;batch-C 50 份已处理;全量(~110M tokens / 2724 份)冻结,等待 System Readiness Gate。Resolver Consumer Adversarial Audit 两轮闭环(R53 第一轮 + R54 第二轮边界攻击);Reference Resolver 保持审查对象,不进生产。**

## 1. 铁律(必须遵守,不可放松)

1. **用中文沟通**——所有面向用户的回复使用中文。
2. **一切结论必须有真实测试证据**;绝不降低验证标准、绝不自我合理化、绝不为失败的测试强行解释、绝不臆测;普遍性结论必须穷举验证。
3. **对抗性变异测试是必需项**(adversarial mutation testing),不是可选项。
4. **每一轮都要写台账**:`log.md`(append-only,只追加不改历史)+ `status.md`,提交、推送、CI 验证三者齐备才算一轮闭环。
5. **恢复性声明必须给出分子/分母/证明方法**(user R47 rule 4)。
6. **PENDING_REVIEW 永不自动转为 PASS**。
7. 审计工具必须遵守两条治理指令(user R50):
   - **Audit Snapshot Manifest**:引用 `R19@sha256(xxxx)` 之类的快照指纹,不引用动态目录;
   - **Input Integrity Gate**:审计前后输入哈希必须相等(边界:Gate 只保护**原件集**;staging 拷贝污染靠**控制组**检查——R51 A3 实证)。
8. **provenance 是一等公民**:`EvidenceProvenance(source_version, source_line, extraction_method, confidence_state)`。
9. 审计结论以用户裁定收口(R42 先例;R53 验收即由用户裁定)。
10. **检测器必须先被真实数据校准再当门卫**(R30 教训;R54 再次实证:R-ACC-14 检查器 schema 误读产生 2210 伪 findings)。

## 2. 仓库与环境

- 仓库:`D:\Project\Papers`;remote `https://github.com/kurt-wong/Aitutors-preprocessing`;gh 身份 `kurt-wong`。
- 当前 main = **R54 提交**(sha 见 git log);前序:`d18307e`(R53)→ `535809b`(R52)→ `d74981c`(R51)→ `d1b6c0a`(R50);冻结基线 `7f37be9`。
- **生产链路脚本(`reslice_pipeline` / `reslice_qc` / `question_identity`)自冻结基线起未动;`scripts/resolver_reference.py` 自 R53 审查通过后保持审查对象身份,零变更。** R54 新增均为审计工具:`scripts/audit_f1_consistency.py`(F1)+ `scripts/r54_round2_attack.py` + `tests/test_audit_f1.py`(+11 CI)。
- 工作目录:`D:\Project\Papers`(与 DSH checkout 分离,勿混)。
- 环境习惯:
  - PowerShell:`$env:PYTHONIOENCODING='utf-8'`;
  - 临时探针写文件;pytest 临时目录用 `.pytest_work/`(`tmp_path` 在本机 sandbox 报 WinError 5 不可用);
  - 写文件用 `write_text(..., newline="")`;
  - **push / gh 需要 escalation**(`sandbox_permissions: danger-full-access` + 一句话 justification);
  - git push 的 stderr 噪音会造成假 exit 1,需甄别;
  - CI 查询:`gh api .../actions/runs`(重定向 `$env:LOCALAPPDATA`);
  - **PowerShell 原生退出码不是布尔**:`git diff --quiet` 后必须检查 `$LASTEXITCODE`;
  - 变异 staging 规范:源文件改名 `src_{name}` + 复制 `.annotated.md` 兄弟文件 + 设置控制组 + 备份/还原并 sha 校验(**绝不 git checkout 未提交内容**)。
- 未提交(有意为之):`data/resolver_ref_r52/resolver_ir.json`(11MB,`resolver_ir.json@sha256:fbcf41ab025fd786614b52d63270160868a2f49ab63121f012905c79f65b04a5`)、**`data/r54_f1/f1_report.json`(4.8MB 逐单元明细,sha256 见已提交的 `data/r54_f1/f1_summary.json` 内 `full_report` 字段)**、`logs/reslice_reslice-pac-annotated_log.txt`、本文件 `RS.MD`。

## 3. 当前阶段:Resolver 审查两轮闭环完成,F1 已实施(Audit Invariant),待用户裁定下一轮

用户 R53 验收裁决已落盘(log.md R54):第一轮验收 🟢;"没有证明 Resolver 正确,而是证明按冻结契约实现时没有发现违反契约行为";**F1 = Audit Invariant only(非 Gate 非 admission rule);STALE 边界维持不扩大;进入第二轮边界攻击而非 rollout**。R54 已执行完毕(F1 落地 + R-ACC-12/13/14),结果待用户验收。

### 3.1 R54 已验证事实(勿重复证明,新主张需新证据)

- **F1**(`scripts/audit_f1_consistency.py`,f1-consistency-0.1):QC 侧(annotated 锚点区间 + 切片区文本)vs resolver 侧(manifest spans × 当前源)四项对账(source_version_sha/行号/span hash)。真实语料控制组 **88/88 文件、2403/2403 单元 MATCH、0 漂移**;294 shared-answer 区 UNCOMPARABLE。灵敏度:代码变异 4/4 咬住(含 Gate sabotage 接线活性);staged manifest 漂移 → F1 DRIFT 而 Resolver 照常 ADMITTED(必要性实证)。
- **R-ACC-12**:stem 尾行丢弃 6/6、answer 错绑 6/6 **全链绿**(QC PASS+ADMITTED+F1 MATCH)——语义正确性只能由 Admission 承接,量化坐实;样本限定(PAC 单文件,K=6/族,不外推发生率)。
- **R-ACC-13**:material 交换/错绑定/丢失 → resolver consumers 与独立重算期望精确相等、文本单份、零重塑;composite 泄漏被 C12 fail-closed;控制组复现原件。
- **R-ACC-14**:真实 IR(528 表单元)消费不变量 I0–I3 **0 findings**;26 键位单元/30 键、502 全 unresolved 单元/**596 unresolved 槽位**(与 R53 单元级口径互洽);负向对照 6/6;**下游默认值攻击面 = 596 槽位**(`answers.get(q,"")` 类朴素消费,登记 C-OUT 消费侧条款候选)。
- **数据形状(重要)**:IR 单元 `answers` = `{cells, method, answers, unresolved}` 表对象(非逐题映射)——R-ACC-14 检查器首版误读产生 2210 伪 findings(审计工具自身缺陷,非 resolver 缺陷),已按真实 schema 重写 + I0 形状检查 + t11 防回归;F1 匹配逻辑另有 1 处缺陷(汇编卷同题号键锚点误消费)由 88 份控制组抓获并修复。
- 套件 **166 passed + 1 xfailed**(本地);**CI Run 34734417644(head `971c887`)= success,149 passed + 17 skipped + 1 xfailed**;`-W error` 下既有 `test_run_paths.py` 有 thread warning(非本轮缺陷,正常口径绿灯)。

### 3.2 冻结契约与关键资产(沿 R53)

- `resolver_contract_design.md`(v0.1 + 附录 B R50 裁决 + **附录 C R54**:F1 定义 + 二轮结果 + 边界)。
- `scripts/resolver_reference.py`(参考 Resolver,审查对象);`scripts/audit_integrity.py`(Gate/快照);IR 以 sha 引用。
- 输入基线 `R50_input_baseline@sha256:795ee1e7…beb`(88 份 356 文件)。

### 3.3 已声明边界(诚实边界,勿越界宣称)

- F1 只证明结构一致性;对语义错误**无检出义务**(R-ACC-12 即为此设计);语义归 QC 语义探针(测量仪)/Admission。
- R-ACC-12/13 结论限定样本域(各 1 份文件,K=6/族),不外推全语料发生率。
- STALE 仅 span 越界信号;Gate 只保护原件集;E1 演示中 Resolver ADMITTED 符合契约(其消费 QC verdict,该态 QC 仍 PASS)。

### 3.4 R55 已验证事实(对 R45 声明的对抗性复证,勿重复证明)

- **顶层声明全部成立**:探针账目 530 单元/78 报警/11 文件(P13:24+P14:32+P15:22)独立重算全等;"0 新缺陷"顶层命题复证——新写独立分类器三方交叉(R45 口头/R46 机器/R55 独立),标签级一致仅 43/78 但分歧全部为同族桶界差异,**族级一致 78/78、跨族 0**;残差 24 条逐条机器证据分诊留档(`data/r55_r45_audit.json`)。
- **c13-02 源卷噪音**行级证据坐实(题干区"共1小题" vs 解析区"共2小题");Q20 printed=None 未伪造;覆盖 22/22 全量穷举全完美(具名 c01-01 30/30、c08-01 44/44、c13-01 34/34);c01-02 28/28 unverified + `PRINTED_LINE` 正则根因逐行验证(c01-01 阳性对照命中);track 22/22 深度字段级可证("人类确实逐题阅读"= 过程声明,机器不可证,如实限定);R45 套件声明经 `294f5c7` 隔离 worktree 重跑 94 passed+17 skipped+1 xfailed(=111−17,算术闭合)+ CI Run 34723840150 success。
- **新发现**:F-r55-2 = **R46 对 R45 的更正自身有分项缺口**(残差 24 条分项之和 23,漏计 c12-02 Q20 `20. （1）铯（2）b（3）a`);F-r55-3 = 分项数字非事实层,今后分诊以**族级账目 + 逐行留档**为准;F-r55-4 = R55 工具自身 2 缺陷(M1 错限 P15、正则不认转义点 `1\.`)由交叉比对抓获并修。
- **变异 5 组全咬合**:staged 工件删报警;真实语料答案值篡改 X→Z(重编译)→ **QC PASS + 探针报警不变**——结构链对答案值级语义错误无检出义务,"0 新缺陷"= 分诊结论而非语料无缺陷证明;工具代码变异 RM1-3 + 还原 sha 闭环。R50 基线 verify 356 文件 0 漂移。
- 套件 **175 passed + 1 xfailed**(本地,CI +9)。

## 4. 待用户裁定的事项(按 R50/R53 优先序)

1. ~~R55 收口~~ ✅(R56 二审裁定通过)。R56/R57 已闭环:G-TAX-1+Rule Retirement Policy → `governance/rule_registry.md`(CI +4 双向钉住);G-RES-1/G-BOUND-1 → `resolver_contract_design.md` 附录 D;G-SCHEMA-1 延期 IR vNext;G-AUD-1 暂不实施。**下一轮(用户裁定路线)= 优先序② BUG-11/14/15 数据卫生(序 11→14→15)**。
2. **优先序②:BUG-11/14/15 数据卫生轮**(R50 用户排序 P1,Resolver 两轮已闭环,是下一顺位)。
3. **优先序③:basis schema-only 实施**(R50 已正式批准:仅检测、违规→REVIEW、绝不静默 PASS)。
4. **优先序④:printed regex 加固**(unknown > 错误确定性)。
5. 其他挂起:C-OUT 消费侧条款(unresolved 显式处理,R54 新登记);R-ACC-12/13 攻击面扩样裁定;PAC 4 个 QC-FAIL 分诊;PAC round-2 扩容;三十一中化学 keep 三方裁决;R19 答案表单元格级切分(528 表单元,26 键位单元/502 全 unresolved 单元/596 unresolved 槽位);BUG-16 历史 EOL 数据;Phase I-4 "42 模糊目标"定义;全量投产冻结;ArtifactWriter Contract 治理(BUG-21/28/29 家族)。

## 5. 恢复动作清单(新会话按序执行)

1. `git log --oneline -5` + `git status --porcelain` 确认 main = R54 提交且工作区符合 §2 末尾的未提交清单。
2. 读 `status.md`(一句话现状 + 当前阶段 + 风险表)。
3. 读 `log.md` 最后 3~5 轮(R51–R54)。
4. 按需读:`resolver_contract_design.md` 附录 C、`scripts/audit_f1_consistency.py`、`data/r54_round2_attack.json`、`data/r54_f1/f1_summary.json`。
5. 向用户复述 §4 待裁定事项,等用户给出下一轮指令后再动手;**不自主开工**。

---

*本文件更新于 R54 收口时;若与 log.md/status.md 冲突,以 log.md(append-only 台账)为准,并请更新本文件。*
