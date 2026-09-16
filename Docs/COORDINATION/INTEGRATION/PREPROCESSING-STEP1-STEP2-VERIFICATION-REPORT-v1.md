# PREPROCESSING Step 1 + Step 2 验证报告(DEC-026 执行令交付)v1

- **Status**: Step 1 COMPLETE / Step 2 COMPLETE / 验证 PASS
- **Authority**: Owner Final Decision Instruction v1(DEC-026)——执行授权 = Step 1 接口快照冻结 + Step 2 `source_content_sha256` 回填 × 87 + 验证报告
- **Identity 字段**: `source_content_sha256` = `SHA256(original source bytes)`,64 字符小写 hex(DEC-025 FC-1 / DEC-026 再确认)
- **基线 commit**: 本报告随 DEC-026 入册 commit 提交;执行脚本 = `scripts/interface_scope_step1_snapshot.py` / `scripts/interface_scope_step2_backfill.py`(确定性、无时间戳、fail-closed、可重入)

---

## 1. Step 1 — 接口快照冻结

**工件**:
- `data/interface_scope_snapshot_step1.json`(接口快照:清单 + hash + R50/IR 关联)
- `data/audit_snapshot_interface_scope_prebackfill.json`(audit_id `interface_scope_prebackfill`,corpus_sha256 = `4ad3458ba11752d53b5885eb727e9da6ee5726b8eac2a5f0b0d81ca22fd19160`,177 文件 = 87 manifest + 87 source + IR + R50 基线 + 快照自身)

**范围口径(冻结)**:字段口径 `identity_version == 2`(兼容 `"2"`),目录面 = `reslice-batch-C`(50)+ `reslice-pac-annotated`(22)+ `resliced-pilot`(15)= **87 份**,与 FC-4 一致;`.pytest_work` 测试拷贝 32 份不入面;目录口径混入 legacy 1 份(`resliced-pilot\高一\化学\2021北京三十一中…(1)`)不在字段口径内。

**冻结时点实测**:

| 维度 | 结果 |
|---|---|
| 接口面份数 | **87** |
| source bytes 在位 | **87 / 87**(`source_file` 全部为可读文件;87 个 source 互不重复) |
| R50 manifest 成员 | **87 / 87**,且记录 sha 与当前 manifest 字节 **87 / 87 一致** |
| R50 source 成员 | **87 / 87**,且记录 sha 与 `source_content_sha256` **87 / 87 一致** |
| IR 关联 | **87 / 87** 有 IR 记录(71 ADMITTED + 16 REJECTED_QC_FAIL) |
| IR hash 一致 | **71 / 71**:`ir.source_sha256` == `SHA256(source bytes)` == `provenance.source_version`(FACT-033③ 今日复验成立) |
| 回填前 sha 键 | **0 / 87**(manifest 已携任何 `*sha*`/`*hash*` 键即抛错,未触发) |

**血统(E2 配对再冻结)**:R50 基线是接口面的成员超集(87/87);自本快照起,接口面的完整性基线角色由 `interface_scope_prebackfill` / `interface_scope_postbackfill` **双快照承接**,R50 基线保留为历史基线(DRIFT 已预期,见 §3)。

## 2. Step 2 — Manifest 字段补齐

**动作**:对 Step 1 冻结的 87 份 manifest 逐份追加一个键:

```
"source_content_sha256": <SHA256(source md 原始字节), 64 小写 hex>
```

**结果**:`n_backfilled = 87` / `n_already_backfilled = 0`。

**写回纪律与证明**:
1. **仅追加一键**:键序 = 原键序 + 新键在尾;序列化风格与在库格式字节级同风格(`json.dumps(ensure_ascii=False, indent=1)`,无尾换行);原子替换(temp + `os.replace`),逐份回读验证 `new_json == old_json + {新键}`。
2. **内容寻址独立证明(事后、全量 87/87)**:将回填后 manifest 剥去 `source_content_sha256` 键重新序列化,其 sha256 **逐份等于 R50 基线记录的回填前 sha**——即除新键外**全部其余字节零改动**(该证明不依赖执行脚本自证,由 R50 历史基线独立锚定)。
3. **语义零触碰**:units / sections / 任何既有键零改动;未动原始文件、IR、Question 数据;`source_content_sha256` 为 Owner 明令授权的回填字段,与"禁止 schema 变更"不冲突(该禁令指未授权变更)。
4. **source 字节不变**:回填前后 87 份 source md sha 与 Step 1 记录值逐份一致(脚本内断言 + post 快照零漂移双证)。

**工件**:
- `data/interface_scope_step2_backfill_report.json`(逐份结果 + 16 份 pending 清单)
- `data/audit_snapshot_interface_scope_postbackfill.json`(audit_id `interface_scope_postbackfill`,corpus_sha256 = `24af8f566e8e2356c29aa99e6b185c5f6f8eaf2df983bd4b6b0669684c240a10`)

## 3. 验证结论(Owner 五、要求的四项)

### 3.1 87 份文件列表
完整逐份清单 = `data/interface_scope_snapshot_step1.json` `rows[87]`(manifest 相对路径 + source_file + hash + R50/IR 关联)+ `data/interface_scope_step2_backfill_report.json` `files[87]`(回填状态 + 键计数)。分布:`reslice-batch-C` 50 / `reslice-pac-annotated` 22 / `resliced-pilot` 15。

### 3.2 hash 一致性检查 — PASS
- **Manifest hash == IR hash(有 IR 者)**:**71 / 71** 成立(ADMITTED 面,`manifest.source_content_sha256 == ir.source_sha256`,含回填后磁盘复读)。
- **Manifest hash == source bytes(全量)**:**87 / 87**(身份 = 内容 hash,path 仅 locator)。
- **source bytes 自快照起零漂移**:pre/post 双快照 + 逐份断言,双证。
- **回填零污染**:剥键重序列化 sha == R50 基线,**87 / 87**。

### 3.3 IR 覆盖情况 — 与 FC-4 一致
- IR 记录 87/87 在册;**ADMITTED = 71**(1,664 单元,语义消费面);**REJECTED_QC_FAIL = 16**(Semantic Pending);REJECTED_V1 = 0(目录口径混入 legacy 1 份不属接口面,记录在 IR 88 条总数内)。
- 16 份**无 provenance/IR 语义对象**(fail-closed 原样,不静默转 PASS);身份层已自足:`source_content_sha256` 已在 manifest(Identity Available / Semantic Pending,DEC-026 §一.4)。

### 3.4 16 份 pending 状态 — Identity Available / Semantic Pending
逐份清单(`data/interface_scope_step2_backfill_report.json` `semantic_pending`,共 16):会考 化学/语文(2);合格考 英语(1);学业水平考试 化学(1);高一 历史/政治/生物/英语(4);高三 化学×2/数学(3);高考真题 数学(1);reslice-pac pac-c07-01 / pac-c09-01 / pac-c09-02 / pac-c11-02(4)。16 份全部已携 `source_content_sha256`,状态 = **Identity Available / Semantic Pending**(DEC-026 §一.4),四保证(可恢复/identity 不变/不新建 identity/不删记录)保持;再生成 IR 属后续批次,**须另令**(本轮未执行)。

### 3.5 R50 DRIFT 对账(E2 预期,已落地)
- `verify R50_input_baseline` → drift = **恰 87 份 manifest**,missing = 0(其余 269 个基线文件零漂移);
- `verify interface_scope_prebackfill` → drift = 同 87 份(历史动作记录);
- `verify interface_scope_postbackfill` → **ok = true**(接口面新配对基线)。

## 4. Freeze 条件核对(Owner 六)

| 条件 | 状态 |
|---|---|
| Step 1 接口快照(清单 + hash + R50 关联) | **DONE**(§1) |
| Step 2 87 份回填 + 逐份验证 | **DONE + PASS**(§2/§3) |
| V3 代码零修改 | 保持(V3 仓本轮零动作) |
| Contract v0.2 Freeze | **待 Claude 完成 C-0a 文字合入 + Owner Freeze 令**(Step 3);DSH 侧前置条件已全部满足 |

## 5. 延期事项(Owner 四、建议,已记录不处理)

legacy 79 份披露 / 17 拒收记录治理 / OCR-PDF 扩展面 / DEC 编号统一 / bytes 传输方式——本轮零动作。
