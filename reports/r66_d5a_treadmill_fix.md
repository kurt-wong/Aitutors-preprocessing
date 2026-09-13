# R66 报告:BUG-14-DATA D5-A — 跑步机切断机制修复(R-OHM-1)

**用户裁定依据(R65 审后指令)**:R65 PASS 收口;D5-A 只修跑步机机制 + 建立修复前冻结快照;
不碰语义去重、不碰 canonical identity、不碰 BUG-14-CHAIN;D5 协议冻结为
D5-A 停跑步机 → D5-B 全量 reclassify 一次 → D5-C 幂等复跑 → D5-D 重审计 → D5-E 语义去重。

---

## 一、修复前冻结快照(先于任何代码改动执行)

武器:`scripts/r66_d5a_snapshot_check.py`(确定性、无时间戳、只读;
复用 r64_data_inventory 同一采集/哈希实现,不另立副本)。

- baseline = `data/r64_corpus_inventory.json`(R64 D0 冻结,R65 已独立复证 0 漂移)。
- 实测:**4,881 / 4,881,changed=0 / missing=0 / new=0**;
  corpus_digest = `6940f2ec994b7f7f653ff5316e9bae1e351177fb22a8f60057c901e7d5821f8d`。
- 身份口径如实声明:(rel_path, size, sha256, norm_sha256);mtime 不入内容身份;
  根级 md 单独点名(F-r65-1 口径延续)。
- daemon 静默监测:`logs/ocr_batch_log.txt` 最后写入 2026-09-10 21:27:45,
  快照前后 mtime 不变(两个 09-10 启动的 python 进程仍在但 2.7 天无日志写入;
  **未杀用户进程**,如实披露)。

## 二、机制修复(治理先行)

1. **登记**:`governance/rule_registry.md` §7 新增 R-OHM-1(先登记后实现,运行规则 #1),
   并载明 runner 自 R25 冻结的**限定解冻声明**(仅新增模块与 main 循环接线)。
2. **新模块** `ocr_service/output_manifest.py`(纯 stdlib,可单测):
   - append-only JSONL 清单:source_rel / source_size / source_sha256 /
     output_rel / written_at / pages;先校验后写 + fsync。
   - `decide_skip`:EXISTS(既有 >100B 语义原样保留)→ 清单判定。
     期望输出落空时:同一 source(size+sha256 级一致)已在册 → **MANIFEST_DONE skip**。
   - fail-closed:清单坏行/缺键/非法类型 → ManifestError → runner 显式
     SystemExit(2),禁止静默降级为重跑。
   - 路径键正斜杠归一(F-r64-1 教训)。
3. **runner 接线**(`ocr_service/batch_convert_pdf.py`,4 处):
   main() 载入清单(fail-closed)/ 循环内 decide_skip 替换旧 exists 检查
   (EXISTS 保持静默,其余决策 `[DECIDE:<reason>]` 显式留证)/ 成功写出即记账
   (清单故障 = FATAL 中止)。`process_pdf` 主体、OCR API 语义、输出路径决策
   **零改动**(t8 源码锚原样在册)。

### 设计裁定(如实入账,非推测)

- **MANIFEST_DONE 不以"记录输出仍在原位"为条件**。首版设计(自 caught)要求
  记录输出现存 >100B 才 skip——但跑步机场景恰恰是输出已被搬走,该分支永不命中,
  切不断回流。修正为:sha 级"已处理"即 skip;记录输出现状(present /
  missing-or-moved)只入日志留证。
- **输出丢失不自动重跑**(t4 钉):自动重跑 = auto-fix,且正是回流污染源;
  重跑权在人——操作者删除对应清单记录即显式授权(t4 实测恢复重跑)。
- **存在性判定顺序不变**:EXISTS 先于清单判定,既有 R25 冻结语义零变化(t1 钉:
  第二轮不新增任何决策日志)。

## 三、测试与对抗(全部真实执行)

- `tests/test_r66_treadmill_fix.py` **10 钉全绿**,核心 t2 集成测试跑
  **真实 batch_convert_pdf.main()**(仅 stub process_pdf,零 API、零网络):
  OCR→记账→模拟 reclassify 搬移→第二轮 main() → `[DECIDE:MANIFEST_DONE]`,
  stub 调用数保持 1、未分类零回流、清单不追加、搬移产物原样。
  CI 无 requests/urllib3 → import 级 stub(测试禁网),如实披露。
- 变异攻击 `.pytest_work/r66_fix_mutation_driver.py`:**5/5 BITE,全部字节级还原**
  (M1 MANIFEST_DONE 改不 skip / M2 坏行静默跳过 / M3 接线回退旧 exists /
  M4 sha 校验拆除 / M5 append 校验拆除)。
- 快照武器阳性控制(t10):字节篡改必入 changed、幽灵记录入 missing、新文件入 new。
- 全量套件:**241 passed + 1 xfailed**(231+10 新钉)。
- **修复后快照重跑:输出与修复前逐字节一致**(sha256 93E77E86…6EF 前后相同),
  corpus_digest 不变 → 机器证据:本轮修复零触碰语料。

## 四、边界与遗留(不夸大)

- runner 本体**未真实执行**(不调 OCR API);证据等级 = 真实 main() 集成 +
  源码锚 + 变异咬合。首次真实运行在用户重启 daemon 后发生。
- 现存两个 09-10 启动的 python 进程持有旧代码;修复对其无效,**需用户重启 daemon**
  才生效。首跑将对既有产出走 EXISTS(静默),对未分类在位文件同样 EXISTS;
  只有"输出不在位 + 清单无记录"的文件会走 OCR——清单从零开始,历史 4,881 份
  产出不在册,**首跑不改变既有 skip 结构**(在位的照旧 skip),之后逐份记账。
- D5-B(全量 reclassify)/ D5-C(幂等复跑)/ D5-D(重审计)/ D5-E(语义去重)
  按协议排期,本轮不启动;reclassify --apply 仍未运行过。

证据:`data/r66_d5a_snapshot_check.json`(修复前后字节一致)、
`governance/rule_registry.md` §7、`tests/test_r66_treadmill_fix.py`、
`.pytest_work/r66_fix_mutation_driver.py`(一次性武器,不入库)。
