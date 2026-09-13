# R64 BUG-14-DATA D0~D5 实测报告(只读审计,零修改生产数据)

- 生成:R64(用户 R63 裁决:进入 BUG-14-DATA,严格 D0→D5,本轮不写清理/归并代码)
- 武器:`scripts/r64_data_inventory.py`(只读、fail-closed、确定性;环境变量覆写仅供测试)
- 证据工件:`data/r64_corpus_inventory.json`(D0)/ `data/r64_unknown_buckets.json`(D1)/
  `data/r64_collision_fingerprint.json`(D2+D3)
- 对抗回归:`tests/test_r64_data_inventory.py` 14 钉 + 武器变异 5/5 咬合(字节级还原)

## D0 — Corpus inventory freeze(实测)

| 口径 | 实测 | 台账 | 一致 |
|---|---|---|---|
| 源树 md(10 目录) | 3,119 | 3,119 | ✅ |
| 派生树 md(9 目录) | 1,762 | — | 首次系统冻结 |
| 顶层 未分类 md | 145 | 145 | ✅ |
| 散落 高三/未分类 md | 2 | (台账未单列) | 新事实 |
| basename 碰撞组(源树) | 73 组 / 146 文件 | 73 | ✅ |
| maintainess\PDF 索引 | 12,707 | 12,707 | ✅ |
| reclassify 搬移审计 | 698 条 | — | 新事实 |

**源树零 manifest**:3,119 份源 md 无一携带 colocated manifest → 源文件身份 = 落位路径
本身(provenance 仅隐式 runner 落位)。这是 BUG-14-DATA 的结构性前提。

## D1 — 145 未分类逐文件归因(机器可复现 bucket)

| bucket | 数量 | 含义 | 证据 |
|---|---|---|---|
| NAME_RULE_COVERED | **141** | 文件名即可被 reclassify 规则覆盖(高考真题 125 / 合格考 15 / 学业水平 1)→ **不是规则缺口**,是"已分类可判但滞留" | `predicates.reclassify_name` |
| └ 其中 dup_twin | 72 | 同名文件已在类型目录存在 → **跑步机回流件** | D2 交叉 |
| └ 其中无孪生 | 69 | 首轮积压件(reclassify 自上次运行后的新到/未跑) | D2 交叉 |
| UNDETERMINED | **4** | 名+正文均无信号 → PENDING_REVIEW(不自动归类) | 见下 |
| stray PLACEMENT_MISMATCH | 2 | 高三/未分类 散落件(文件名含"高三"),孪生在 其他汇编/理综 | reclassify EXTRA_DIRS 口径 |

4 份 UNDETERMINED 明细(全部是**真实规则缺口**,各不相同):
1. `未分类/物理/2022北京人大翠微学校高—10月月考物理…` — **"高—"笔误**(应为"高一",runner 正则 `高一|高1` 不覆盖)
2. `未分类/物理/2022北京人大附中翠微学校高—10月月考物理…` — 同上(另一学校名写法)
3. `未分类/化学/19_2023重庆市巴蜀中学高考适应性月考卷…` — "高考适应性月考"非"高考真题",GAOKAO_RE 不覆盖
4. `未分类/语文/2023北京一七一中初三（上）第一次月考语文…` — **初三(初中)**,学段越界,属 corpus admission 问题

147 份(145+2)中 143 份带下载重复后缀 `(N)`;全部 147 份 PDF 侧 exact stem 命中(PDF 真实存在)。

## D2 — 73 碰撞组指纹分层

| 层 | 实测 |
|---|---|
| byte-identical(SHA-256 全同) | **6 组** |
| 仅归一化相同(NFC/换行/rstrip 后同) | 0 组 |
| byte-different | **67 组** |
| 不可读 | 0 组 |

mtime 时序(事实,非因果判定):未分类份更晚 **68** 组;高考真题份更晚 2;其他汇编份更晚 2;学业水平份更晚 1。

## D3 — duplicate source 真实性(四层机器证据)

```
basename 相同(73 组)
  ↓ SHA-256:6 组全同 / 67 组不同(两次独立 OCR 产物)
  ↓ 归一化文本:无新增相同(67 组连文本归一化后仍不同)
  ↓ PDF 侧:73/73 exact stem 在 maintainess\PDF 命中(同名 PDF 唯一/存在)
  ↓ 搬移审计:73/73 出现在 reclassify_audit.jsonl(698 条搬移记录)
```

**跑步机机制实锤(结构证据链,非推测)**:
1. reclassify `--apply` 把 X.md 从未分类/科目 **搬移**到类型目录(审计在册 73/73);
2. runner skip-check 只查 `未分类/科目/X.md` 是否存在且 >100B → 搬移后落空;
3. 同一 PDF 重 OCR → X.md **回流**未分类(mtime 更晚 68/73,字节不同 67/73);
4. 循环往复 = "未分类跑步机",且每转一圈烧一次 OCR 配额、多一份重复源。

**是否同一 logical source(语义层)**:67 组字节不同份属"同一 PDF 的两次 OCR",
但"保留哪一份/是否等价"属业务语义 → 一律 **PENDING_REVIEW**,禁止自动归并。

## D4 — runner 边界攻击(合成夹具,零 API 调用,14 钉全过)

runner 的 source identity = **输出路径存在且 >100 字节,仅此而已**:

| 攻击 | 实测结论 |
|---|---|
| 搬移后重跑(t12) | skip-check 落空 → 重 OCR(跑步机机制复现钉) |
| 同名不同内容(t11) | 第二份被静默跳过(无内容指纹) |
| 净化碰撞 `a<b`/`a>b`(t13) | 同一输出名 → 后者静默跳过 |
| 大小写差异(t14,win) | `exists("x.md")` 判真 `X.md` → 静默跳过 |
| 文件名笔误"高—"(t10) | 未分类(规则缺口钉) |
| 学段越界"初三"(t10) | 未分类(admission 缺口钉) |

源码锚(t8/t9):runner/reclassify 关键行原文在册,副本逻辑漂移即红。

## D5 — 修复决策(仅决策,不实施;全部待用户裁定)

**结论:BUG-14-DATA 不是"一个 bug",是 1 个机制缺陷 + 4 类数据事实:**

| # | 事实 | 建议处置域 | 备注 |
|---|---|---|---|
| 1 | **跑步机机制**(搬移击败 skip-check) | runner 侧最小修复候选:skip-check 咨询 reclassify_audit 搬移目标 / 或 runner 自维护输出清单 | **先修机制再谈清理**:否则任何一次 reclassify 都会触发 N 份重 OCR(烧配额+造新重复) |
| 2 | 69 份首轮积压 | 机制修复后的周期 reclassify | 现在直接跑 --apply 会触发 145 份重 OCR,**不建议** |
| 3 | 4 份规则缺口(高—×2 / ��考适应性月考 / 初三) | 用户逐份裁定(正则归一化?admission 排除?) | PENDING_REVIEW |
| 4 | 67 组重 OCR 孪生 + 6 组字节全同 | 语义裁定哪份 canonical → 才能去重 | PENDING_REVIEW,禁自动归并 |
| 5 | 2 份高三/未分类 散落 | 并入 #1 修复域(placement 审计) | — |

**本轮未做(按用户裁定)**:未跑 reclassify、未移动/删除任何文件、未改 runner、未归并任何重复。
