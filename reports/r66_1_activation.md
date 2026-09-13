# R66.1 Runtime Activation Verification(D5-A 生效验收)

日期:2026-09-13 | 轮次:R66.1 | 依据:用户 R66 裁定(PASS,code-level complete,runtime activation pending)
裁决原话:「重启旧 daemon → 做一次最小真实运行验证 → 第二次运行证明 MANIFEST_DONE 且不发生 OCR。在这三项证据拿到之前,禁止 D5-B reclassify --apply。」

## 0. 结论摘要

| 项 | 状态 | 证据 |
|---|---|---|
| 旧 daemon 进程归属取证 | ✅ | §1 |
| 旧 daemon 停止(卡死实锤) | ✅ | §1 |
| 激活前风险预检(发现引导缺口) | ✅ | §2 |
| B 首次真实运行(真实 OCR API + manifest 落账) | ✅ 沙箱受控 | §3 P1 |
| C 二次扫描零 OCR | ✅ 沙箱受控 | §3 P2 |
| C' 搬移复扫 MANIFEST_DONE 零 OCR(跑步机切断,真实运行时) | ✅ 沙箱受控 | §3 P3 |
| A 生产 daemon 重启 + 新代码进程归属 | ⛔ 暂停,待用户裁决 | §4 |

**生产 daemon 未重启**——预检发现直启将触发约 10,282 份真实 OCR(含 625 份历史上已处理过、输出被搬走的受害者重复 OCR),超出「最小验证」范围,须用户裁决(§4)。**D5-B 继续禁止。**

## 1. 进程归属(R66.1-A 前半)

重启前取证(Get-CimInstance 命令行 + Get-Process 路径/启动时间):

| PID | 命令行 | 解释器 | 启动时间 | 处置 |
|---|---|---|---|---|
| 38160 | `python ocr_watchdog.py` | Python312\python.exe | 2026-09-10 21:21:06 | 已终止 |
| 33036 | `python D:\Project\Papers\ocr_service\batch_convert_pdf.py` | Python312\python.exe | 2026-09-10 21:27:06 | 已终止(看门狗被杀时同时消失) |
| 42124 | `pythonw -m hermes_cli.main gateway run` | — | 2026-09-13 01:00:28 | 无关进程,未触碰 |

**runner 卡死实锤**:`logs/ocr_batch_log.txt` 停笔于 2026-09-10 21:27:45(扫描至 75/12703,当日已用 6481/20000 页),进程存活 2.7 天零输出——持旧代码且已 stalled,终止即止损。终止顺序:先看门狗后 runner(防 5 分钟自动重拉)。

**今日配额 293 页来源澄清(矛盾排查)**:`data/ocr_page_usage.json` mtime=2026-09-13 01:11:38,与 `Ocr-markdown\reslice-pac\ocr\pac-c*.md` 26 个文件的写入时间(01:11:22–01:11:38)完全吻合 → 系 reslice-pac 流水线自身 OCR 步骤所耗,**与批量 daemon 无关**(daemon 日志同期零输出)。

## 2. 激活前风险预检(只读,发现清单引导缺口)

武器:`scripts/r66_1_preflight.py` + `scripts/r66_1_victim_split.py`(确定性,零 API)。

- 全量 12,703 PDF,EXISTS 在位 skip 仅 2,421;**首扫将真实 OCR 10,282 份(源 20.2 GB)**——清单从零开始,历史被搬移输出的 source 无记录可查,这正是**引导缺口(bootstrap gap)**:R-OHM-1 只保护"记账之后",不保护"记账之前"。
- 拆分(匹配规则:md 文件名去 .md == sanitize_stem(pdf),精确等值,runner 自身输出路径语义,非语义去重):
  - **625 份跑步机受害者候选**(语料中已有同名 md,489 MB):历史已 OCR、输出被搬移;直启重 OCR = 重复产出 + 配额浪费 + 语料污染;
  - **9,657 份从未处理**(19.7 GB):daemon 本职待办(配额 20,000 页/日闸门约束)。
- 证据:`data/r66_1_preflight.json`、`data/r66_1_victim_split.json`。

## 3. 受控激活验证(真实 runner、真实 OCR API、沙箱目录)

武器:`scripts/r66_1_activation_driver.py`。**不改任何生产代码**:import 真实 `batch_convert_pdf` 模块,仅在驱动进程内重定向 PDF_ROOT/OUTPUT_ROOT/MANIFEST_FILE/LOG_FILE 至 `.pytest_work\r66_1_activation\`;`PAGE_USAGE_FILE` 保持生产路径,真实页数诚实入账。source = 真实 PDF 沙箱副本(`2022北京西城高二（下）期末地理参考答案(1).pdf`,228,485 字节,sha256 dd239c…);Ocr-markdown 零写入,语料零触碰。

| 阶段 | 动作 | 实测结果 |
|---|---|---|
| P1 首跑 | 真实 OCR | `[DECIDE:NO_MANIFEST_ENTRY]` → `[OK] 2 pages` → output 写出 + manifest 0→1 条(含 source_sha256/pages);配额 293→295 诚实记账 |
| P2 复扫 | output 在位 | EXISTS 静默 skip,manifest 字节不变,零 OCR |
| P3 搬移复扫 | 移走 output(模拟 reclassify) | **`[DECIDE:MANIFEST_DONE]`(recorded_output_status="missing-or-moved")→ 零 OCR、零回流、manifest 不变** |
| P4 归位 | output 移回 | manifest 不变 |

verdict 4/4 true;证据全文 `data/r66_1_activation_evidence.json`。这是**跑步机切断在真实运行时(非测试桩)的直接证据**:t2 测试用 stub process_pdf,此处为真实 API 闭环。

## 4. 生产重启暂停理由与用户裁决点

直启看门狗 = 首扫对 10,282 份真实 OCR(其中 625 份为重复),不符合「最小验证」,且 625 份重 OCR 会在 runner 路径重新落 md,与已被搬移的旧输出形成内容重复(污染面留待 D5-E 收拾,主动制造不可接受)。选项:

- **甲、审计记录引导(推荐候选)**:用 R63 reclassify 审计日志(698 moves,from→to 有案)把「log 可证的 source→已处理输出」回填 manifest(证据级引导,非猜测;回填工具须新轮治理:登记+测试+变异);匹配不上的受害者保持 NO_MANIFEST_ENTRY 如实重跑或点名上报。
- **乙、接受直启**:按 daemon 本职恢复全量 OCR(配额闸门约束),625 份重复如实入账,污染留 D5-E;成本透明但违背最小干预。
- **丙、维持停机**:先做引导工具再统一激活。

无论选哪项,激活后验收同一套:进程归属(新 PID/工作树/HEAD)+ manifest 建立 + `[DECIDE:*]` 轨迹。

## 5. 本轮其他落盘

- R-OHM-1 语义边界写死(用户 R66 裁定 §4):`ocr_service/output_manifest.py` 模块头 + `governance/rule_registry.md` §7——manifest = processing history(证明"已成功执行过 OCR"),**不是** output availability index;禁止未来以"恢复丢失输出"为由加自动重跑 fallback。
- 全量回归:242 passed + 1 xfailed(与 R66 收口态一致,零回退)。

## 6. 边界(如实)

- §3 证据等级 = 真实 API + 真实 runner 代码路径,但根目录为沙箱;**不等于**生产 daemon 已切换新代码(A 项未完成)。
- 625/9,657 拆分基于同名 stem 精确匹配(runner 输出路径语义),是**风险预检口径**,不构成对这 625 份"确实已处理"的逐份裁定;引导回填若实施须逐份日志证据。
- D5-B/C/D/E 未启动;BUG-14-CHAIN/canonical identity/语义去重保持冻结。
