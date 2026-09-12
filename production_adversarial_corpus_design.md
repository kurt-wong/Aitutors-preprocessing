# Production Adversarial Corpus 设计稿(Gate 首攻面:真实 OCR + 真实 LLM 生产链)

> 立项:2026-09-13(R43,依 R42 用户裁定第一优先级)。状态:**PLANNED — 须用户批准样本量/成本预算后启动**。
> 定位:System Readiness Gate 首攻面的证据基座。当前大量证据证明的是 deterministic post-processing;本语料补的是**生产入口真实行为**——OCR 服务链 + LLM 语义批注 + 真实源噪声(R29 D6:OCR 服务链零测试;D7:真实 MIMO 准确率未自动化证明)。

---

## 1. 目标与非目标

**目标**:对每份对抗样本,记录从源文件到最终处置的**全 stage 轨迹**,而不是只看终局 PASS/FAIL:

```
source → OCR → annotation(LLM) → manifest → QC → identity check → artifact → [下游消费]
```

每个 stage 记录:输入指纹(sha256)、输出指纹、耗时、失败/告警、以及**人工语义复核裁决**(对照 PDF 原卷)。

**非目标(明确不做,防范围蔓延)**:
- 不追求数量(第一轮用户裁定:不追求数量);
- 不做全量推广、不跑生产队列(12,707 份守护队列不动);
- 不发明新 QC 规则、不改 Identity 冻结层——发现的缺陷入 `bugs.md` 走既有裁决流程;
- **Resolver / Compiler / Gate / Admission 尚未构建**——对应 stage 轨迹如实记 `NOT_BUILT`,不得伪造"端到端通过"。当前可测的真实链条 = source → OCR → annotation → manifest → QC → identity → artifact。

## 2. 事实基座(2026-09-13 实测,选样前提)

| 事实 | 数字/结论 | 出处 |
|---|---|---|
| 原始源格式分布(`original` 树) | PDF 38,893 / DOCX 30,254 / DOC 207 / PPTX 164 / 独立 JPG+PNG 各 1 | `Get-ChildItem original -Recurse` 实测 |
| OCR 生产队列 | `maintainess\PDF` 12,707 份纯 PDF | 实测 |
| OCR 服务 | PaddleOCR-VL-1.6(aistudio API),日额度 20,000 页,`data/ocr_page_usage.json` 记账 | `ocr_service/batch_convert_pdf.py` |
| LLM 批注成本(R17 实测) | ≈37,200 tokens/份(均值)、串行 ≈290s/份;8 路并发 93.4s/份 | log.md R17 |
| 会考/known-hazard 素材 | BUG-24/25 台账已定位真实坏形态文件(行融合、straddle、`\.` 转义点、丢节) | bugs.md |

**推论**:"图像输入"类无独立 JPG/PNG 源(各 1 张),**以扫描 PDF 承载**;"DOCX"类须先确认 DOCX→PDF 归一路径(`maintainess\DOCX`、`待转换DOC` 存在,但 OCR 服务只吃 PDF)——**启动前置检查项 P-2**,未确认前该类标记 BLOCKED,不得假装已覆盖。

## 3. 对抗样本类别(13 类,用户裁定)

| # | 类别 | 攻击面 | 选样来源 |
|---|---|---|---|
| C1 | PDF 原生文本 | 基础路径(非扫描,OCR 对文本层的行为) | original 树文本层 PDF |
| C2 | OCR 扫描 PDF | OCR 噪声主战场 | 队列内已知扫描件 |
| C3 | DOCX | 文档结构差异 | maintainess\DOCX(依赖 P-2) |
| C4 | JPG/PNG 图像 | 图像输入 | 现实仅扫描 PDF 承载,如实记录 |
| C5 | 数学 LaTeX | 数学表达 | 裸 LaTeX/半定界高发卷(BUG-15 素材) |
| C6 | 化学图片题 | material/figure | 化学卷(含 `\ce{}` 消费方提醒) |
| C7 | 答案与解析混排 | region binding | 详解复述型卷(BUG-17 家族素材) |
| C8 | 跨页题 | span continuity | 双栏/跨页卷 |
| C9 | 多 section 同号题 | identity | 选考模块/汇编卷(合法形态) |
| C10 | 题图与正文分离 | material binding | 配图漂移素材(R17 Q9 卫星锚) |
| C11 | OCR 行融合 | SectionLocator | 三十一中化学 L324 同类 |
| C12 | OCR 错号 | identity uncertainty | 8 例 `\.` 转义点同类 |
| C13 | 复杂 composite | question boundaries | 复合题最密集卷(人大附中地理类) |

**选样纪律(硬约束)**:
1. **真实源,禁止合成**——R30 教训:合成 fixture 覆盖不了真实卷的编号花样;
2. 每类样本必须**先有 hazard 证据再入选**(台账已知坏形态文件优先),禁止"随便挑一份当代表";
3. 样本一旦选定**只字不改地留档**(路径 + sha256 + 页数),后续任何轮次用同一样本,保证可复现;
4. known-hazard 样本的期望行为 = **该坏形态必须被如实暴露**(FAIL/PENDING_REVIEW 或人检发现问题),而不是"跑完就算过"。

## 4. 全 stage 轨迹 schema(每样本一份 `data/pac_track_<id>.json`)

```json
{
  "sample_id": "pac-c02-01",
  "category": "C2 扫描PDF",
  "source": {"path": "...", "sha256": "...", "pages": 12, "format": "pdf"},
  "stages": {
    "ocr":       {"status": "OK|FAIL|SKIPPED", "job_id": "...", "pages_billed": 12, "duration_s": 0, "output_md_sha256": "...", "notes": ""},
    "annotation":{"status": "...", "prompt_version": "v2.3", "model": "mimo-x-pro-preview", "tokens_in": 0, "tokens_out": 0, "attempts": 1, "duration_s": 0},
    "manifest":  {"status": "...", "units": 0, "identity_version": 2},
    "qc":        {"status": "...", "verdict": "PASS|FAIL", "issues": []},
    "identity":  {"status": "...", "fails": 0, "reviews": 0},
    "artifact":  {"status": "...", "slices_sha256": "..."},
    "resolver":  {"status": "NOT_BUILT"},
    "compiler":  {"status": "NOT_BUILT"},
    "gate":      {"status": "NOT_BUILT"},
    "admission": {"status": "NOT_BUILT"}
  },
  "human_review": {"verdict": "...", "evidence": "对照 PDF 原卷逐题人检", "notes": ""},
  "findings": []
}
```

**裁决纪律**:① 任一 stage FAIL 必须向后传播可见,禁止静默转 PASS(B 攻击面原则);② 人工复核按 `review_protocol.md` 规则 2 三列制记录;③ 发现的新缺陷走 bugs.md 流程,本语料只负责暴露。

## 5. 成本估算(第一轮,每类 1 份 ≈ 13 份)

| 资源 | 估算 | 依据 |
|---|---|---|
| OCR 页额度 | ≈150–250 页(13 份 × 8–20 页) | 日额度 20,000 页的 1–1.5%,一次性 |
| LLM tokens | ≈50 万(13 × 37.2k 均值;按卷大小 ±2× 浮动) | R17 实测均值 |
| 墙钟时间 | 串行 ≈1 小时;8 路并发 ≈15–25 分钟 | R17 实测 290s / 93.4s |
| 人工复核 | 13 份逐题人检(主要成本是人的注意力,不是钱) | — |

第二轮扩样(每类 2 份 ≈ 26 份)在第一轮分诊结论出来后再定。

## 6. 启动前置检查(全部 🟢 才开跑)

- **P-1 用户批准**:样本量(13 / 26 / 自定)+ LLM 成本 + OCR 页额度消耗;
- **P-2 DOCX→PDF 归一路径确认**(C3/C4 依赖;确认不了就如实缩范围并声明);
- **P-3 OCR 守护进程/队列状态确认**:`ocr_page_usage.json` 停留在 2026-09-10(used 6639),守护由用户手动启动——本轮小批量是否直接调 API 单跑,需与用户对齐,避免与守护队列撞额度;
- **P-4 输出隔离**:对抗语料产物写独立目录(如 `Ocr-markdown\reslice-pac`),不混入生产交付范围(66 份),QC/口径账目分开记。

## 7. 与 Gate 其余攻击面的关系

本语料是 ① 真实 OCR+LLM 链的证据基座;② BUG-11/14/15 数据卫生、③ D-02 可移植性、④ 失败传播按用户裁定顺序跟进。三十一中化学 keep 三方裁决并行独立,不进入本语料的通过条件。
