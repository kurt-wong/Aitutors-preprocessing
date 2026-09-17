# D2/D3/D4 Decision Brief — Evidence First, No Self-Fix

> Round: DSH `DEC-049`(2026-09-17)
> Directive: Owner 令「基于 DEC-048 及此前 Consumer Boundary 审查记录,暂停 D2/D3/D4 的最终裁决;Owner 当前并不知道 D2/D3/D4 各自具体代表什么问题,必须把三个问题的原始技术争议还原出来」。
> Review object: V3 `cc12d79e9a22f6274100ea0bb61f92493ba88509`(本地 V3 仓 HEAD 亲验 = `cc12d79`;M1–M5 五模块 sha256 与 DEC-048 锚逐一 MATCH:`1ca33a45a101de8c`/2811B · `803c4ed8a93f59b5`/1877B · `f960b513a935c8ca`/6430B · `1306105c6c3d2b8b`/3725B · `8a5d267e285800f0`/6163B)。
> Frozen object: `PREPROCESSING-V3-CONTRACT-v0.2-DRAFT.md` @ f4941ff,sha256 `9c6b9063e81fb2a66d85794b280c9d931f1b0074b39abf472033218149b17528` / 92,197B(本地副本本轮亲验 MATCH)。

## §0 纪律与读法(先于一切结论)

1. **名称不等于问题定义**。"D2/D3/D4" 只是登记编号;本文件按证据还原每个编号背后的**原始技术争议**,不以编号或标签代替问题陈述。
2. **本轮零裁决**。本文档不选择任何解释 A/B;不修改代码、不修改 Frozen Spec、不修改 Producer、不修改 V3 任何文档;不以"测试通过"充当 Owner Decision(canonical 1780 passed 仅作行为背景,不构成任何 D 项的裁决依据)。
3. **权威层级(取证事实,非解释)**:
   - 唯一 Owner 冻结对象 = Contract v0.2(`9c6b9063…7528`)。其全文对 M1–M5 的 **Python 级签名零规定**(`SourceBytes`/`raw_bytes`/`bytes_source`/`evaluate_identity` 等标识符 grep = 0 命中);它冻结的是**能力与行为**(§0.1 ⑥ / §2.3 / §5.6.2),不是函数名/字段名/异常类名。
   - Design v1.1(`PREPROCESSING-V3-CONSUMER-IDENTITY-VERIFICATION-DESIGN-v1.1.md`)§4.7 原文自述:「以上签名、类型、异常、状态码**已冻结**。实现阶段直接使用,不得修改。**任何修改须 Owner 另行下令**。」——该"冻结"是 **V3 侧自述冻结**,不是 Owner 冻结令;且经 `git ls-files`(cc12d79)证实该文件**不在 git 追踪集**(CONTRACTS 目录 tracked = 9 份,DESIGN v1/v1.1 均不在列,untracked 工作树文档)。
   - Owner Truth Table(DEC-042 聊天指令,历轮再确认):VERIFIED+AVAILABLE→PASS;VERIFIED+PENDING→BLOCK;VERIFIED+None→BLOCK;FAILED/INVALID any→BLOCK。
4. 三项 D 的"Frozen Spec 对应章节"与"Contract 对应章节"在本生态中**指向同一份文件**(唯一 Frozen Spec ≡ Frozen Contract v0.2);下文 §3/§4 分别给出「冻结条款原文」与「该 Contract 对本争议点是否有规定(含零规定的 grep 证据)」,不虚构第二份冻结文件。
5. **取证可复核性**:全部代码/文档引用带文件路径 + 行号 + hash 锚;Design/Contract 原文为逐字引用;所有"未规定/零命中"均有 grep 证据。

---

## D2 — M2 Raw Bytes Loader 的接口形状(数据类字段 + 异常类型 + 函数名 + 模块路径)

### D2.1 首次发现来源

`Docs/COORDINATION/INTEGRATION/PREPROCESSING-PRODUCER-GUARDIAN-M5-BOUNDARY-REVIEW-v1.md` §10(DSH DEC-042 审查轮,2026-09-16,审查对象 = Claude 本地 untracked 快照),登记表第 D2 行;同轮 `CURRENT.md` DEC-042 块 ④ 同步登记。后续 DEC-043(`…M5-REVIEW-ADVERSARIAL-v1.md` L106)、DEC-047(`…CONSUMER-BOUNDARY-CLOSURE-REVIEW-v1.md` L120)、DEC-048(`…PHASE25-GUARDIAN-REVIEW-v1.md` L139)三轮维持 OPEN,接口面 hash 锚三轮未动(M2 = `803c4ed8a93f59b5`/1877B,DEC-047 与 DEC-048 均亲验)。

### D2.2 原始 observation / discrepancy(原文照录)

> | D2 | M2 接口 | `RawBytesIdentity(raw_bytes, sha256)` + `SourceBytesNotFoundError/SourceBytesReadError`(§4.3) | `(bytes_source, sha256)`(不保留 bytes)+ 裸 `FileNotFoundError/OSError` | 接口偏离 |
> —— M5-BOUNDARY-REVIEW-v1.md L178

### D2.3 Frozen Spec 对应章节及原文(Contract v0.2 冻结条款)

§0.1 冻结内容 ⑥(Source Bytes Capability,binding):

> 「V3 **必须能获得 raw bytes 并重算身份键验证**(fail-closed);**不冻结传输方案**」;能力四条含「可获得 raw bytes——Interface Scope 内每份 source,V3 有办法取得其原始字节(不是 canonical_json 包裹、不是 splitlines 规范化文本)」「可重算并验证——V3 用标准库对 raw bytes 独立重算 SHA-256,与 producer 声明值比对」(§2.3,DEC-029 原则 6 + DEC-030 Decision 2 + DEC-031 终局确认)。

### D2.4 Contract 对应章节及原文(同文件,实现边界面)

§5.6.2 Consumer Implementation Boundary(REQUIREMENT):

> 输入:`Manifest + raw bytes + IR`;验证:`Manifest identity(重算 SHA256(bytes) == Manifest.source_content_sha256)`;失败:`fail-closed(任何关键验证失败 → 阻断消费,不得继续向下游)`;成功:`进入既有 V3 Gate / Admission 链`。

**Contract 对 M2 Python 签名的规定 = 零规定(grep 证据)**:在 `PREPROCESSING-V3-CONTRACT-v0.2-DRAFT.md` 中检索 `SourceBytes|raw_bytes|bytes_source` = **0 命中**。即:冻结契约钉的是「能拿 bytes、能重算、fail-closed」,**不钉** dataclass 字段名、不钉异常类、不钉函数名、不钉模块路径。

### D2.5 Design 对应章节及原文(Design v1.1 §4.3,自述冻结文本)

> ```
> 文件: backend/scripts/preprocessing_consumer/identity/raw_bytes_loader.py
> @dataclass(frozen=True)
> class RawBytesIdentity:
>     raw_bytes: bytes                    # 原始字节,保真 CRLF/BOM/trailing newline
>     sha256: str                         # 64-char lowercase hex = SHA256(raw_bytes)
> class SourceBytesNotFoundError(Exception): ...
> class SourceBytesReadError(Exception): ...
> def load_raw_bytes(source_path: Path) -> RawBytesIdentity:
>     异常: SourceBytesNotFoundError — 文件不存在
>           SourceBytesReadError — 文件读取失败
> ```
> §4.7:「以上签名、类型、异常、状态码**已冻结**……任何修改须 Owner 另行下令。」

### D2.6 当前 `cc12d79` 实现

`backend/app/core/raw_bytes_identity.py`(sha256 前缀 `803c4ed8a93f59b5`,1877B):

- L25-33:`RawBytesIdentity(bytes_source: str, sha256: str)` —— **不保留 bytes**,`bytes_source` 注释自declared「locator,非 identity」;
- L36-54:`load_raw_bytes_identity(source_path)`;`raw_bytes = source_path.read_bytes()` + `hashlib.sha256(raw_bytes).hexdigest()`(L49-50,满足 Contract §2.3 重算口径);
- L45-47:Raises `FileNotFoundError` / `OSError`(裸内建异常,无自定义类);
- 模块路径 = `app/core/`,非 Design 的 `scripts/preprocessing_consumer/identity/raw_bytes_loader.py`;函数名 = `load_raw_bytes_identity`,非 Design 的 `load_raw_bytes`。

### D2.7 对应测试

- `backend/tests/test_raw_bytes_identity.py`:L126 `assert id_.bytes_source == str(p)`(钉现行字段);L141-143 `test_missing_file_raises` 钉 `pytest.raises(FileNotFoundError)`(钉裸异常);L41-118 行为组(CRLF≠LF / trailing newline / unicode / BOM / text-hash≠bytes-hash)= 与 Contract §2.3「非规范化、保真原始字节」逐条一致。
- `backend/scripts/preprocessing_consumer/runner_b2.py` L77-86:`except (FileNotFoundError, OSError)` → 返回 BLOCK(`mismatches=("source_bytes_error",)`)——现行接线依赖内建异常类型。

### D2.8 具体冲突 / 歧义是什么

Design v1.1(自述冻结)与实现之间**四重偏离**:① dataclass 不保留 `raw_bytes` 而以 `bytes_source`(路径字符串)替代;② 异常 = 裸 `FileNotFoundError/OSError` 而非 `SourceBytesNotFoundError/SourceBytesReadError`;③ 函数名 `load_raw_bytes_identity` ≠ `load_raw_bytes`;④ 模块路径 `app/core/` ≠ `scripts/preprocessing_consumer/identity/`。**行为方向无分歧**:两边都 fail-closed(文件缺失/读失败 → BLOCK),且现行实测满足 Contract §2.3 全部四条能力(DEC-044/048 行为电池 + 活体 71/88 全链)。歧义的本质:**"冻结接口"一词在 Design v1.1 中是 V3 自述,而 Owner 冻结对象(Contract)从未钉过这一层**。

### D2.9 为什么属于 Owner Decision,而不是普通 implementation defect

- 普通 implementation defect 的判据 = 违反冻结对象或行为 fail-closed 被破坏。**两者都不存在**:Contract 零规定该签名(grep 证据 D2.4),行为面 fail-closed 实测成立。
- 冲突双方 =「实现」vs「一份自述冻结的 untracked 设计文档」。收口只有两条路:改 Design(→v1.2 追认实现)或改实现(→回到 Design 签名)。Design §4.7 明文「任何修改须 Owner 另行下令」;DSH 纪律 = 不写 Consumer 代码、不改 V3 文档、不自行解决 authority conflict(DEC-048 指令⑥)。**两条路都在 Owner 权限内,任何一条都不在 DSH 权限内**。
- 附带的实质取舍(保留 bytes 与否)关系 §0.1 ⑥ 能力的**接口表达形态**(bytes 在 M2 产物中直接可得 vs 需再次读盘),属架构形态选择,非 bug。

### D2.10 合理解释(全部列出)

- **解释 A(追认实现)**:实现是面向真实链的有意简化——M2 消费点(runner_b2)只需要 computed sha,保留 bytes 徒增内存;裸异常由 runner 兜底捕获且方向安全;Design v1.1 应在 v1.2 中改写为现行签名。支撑证据:M2 行为测试组全绿、runner 接线即为内建异常、模块 docstring 已注明设计依据与禁止项且行为全部遵守。
- **解释 B(回到 Design)**:Design §4.7 自述冻结且明文「实现阶段直接使用,不得修改」;`SourceBytes*` 自定义异常给出**精确 catch 面**(裸 `OSError` 覆盖面过宽,未来调用方易误捕/漏捕);dataclass 保留 `raw_bytes` 是 Contract §0.1 ⑥「可获得 raw bytes」能力在接口层的直接物化(未来传输/二次校验/审计重放都需要 bytes 在产物中)。支撑证据:Design 文本、Contract 能力条款字面、自定义异常的类型安全价值。
- (A/B 的混合变体——仅引入 `SourceBytes*` 异常子类、或仅保留 `raw_bytes` 字段——同属 Owner 可选项,一并列出,不单列编号。)

### D2.11 每种解释的影响

| 影响面 | 解释 A(追认实现) | 解释 B(回到 Design) |
|---|---|---|
| Consumer Boundary | 无变化(现行为已被 DEC-044/048 全链验证) | 无行为变化;接口重构 = V3 代码 + 测试改动,Claude 执行 |
| fail-closed | 不变 | 不变(异常类型变化不改变 BLOCK 结果;runner 需同步改 catch 面) |
| 数据模型 | 无(不涉 DB / manifest / IR) | 无(同上);仅 Python 产物形状 |
| 后续阶段 | 未来需要 bytes 的消费方(审计重放/二次校验)须重新读盘并自证字节一致 | bytes 在 M2 产物中直接可得,利于后续能力 |
| 文档面 | Design v1.2 修订(V3 侧 docs-only) | Design 不动;实现+测试改动 |

### D2.12 Guardian conformance analysis

两种收口**都不违反** Frozen Contract(§0.1 ⑥/§2.3/§5.6.2 在两种形状下均满足——能力已实测,重算口径 = `hashlib.sha256(read_bytes())` 两边同源);都不触碰 Producer / 冻结对象;都不改变 Owner Truth Table 的生效结果。DSH 按纪律**只陈述符合性,不选择**;选择本身即 Owner 令。

### D2.13 Owner must decide

> **Owner must decide:D2 —— M2 接口面以哪份为准收口:解释 A(修订 Design v1.2 追认现行实现:`RawBytesIdentity(bytes_source, sha256)` + 裸 `FileNotFoundError/OSError` + `load_raw_bytes_identity` @ `app/core/`)还是解释 B(按 Design v1.1 §4.3 令 V3 改实现:保留 `raw_bytes` + `SourceBytesNotFoundError/SourceBytesReadError` + `load_raw_bytes` @ `scripts/preprocessing_consumer/identity/`),或明示混合变体;并明确该收口令的执行者(V3/Claude)与验收方式。**

---

## D3 — M3 IR Identity Reader 数据类字段名(`source_content_sha256` vs `source_sha256`)

### D3.1 首次发现来源

同 D2:M5-BOUNDARY-REVIEW-v1.md §10,登记表第 D3 行(DEC-042 轮);DEC-043/047/048 三轮维持 OPEN,`ir_identity.py` hash 锚 DEC-047(`f960b513a935c8ca`/6430B)与 DEC-048 亲验一致。

### D3.2 原始 observation / discrepancy(原文照录)

> | D3 | M3 字段名 | `source_sha256`(§4.4) | `source_content_sha256` | 接口偏离 |
> —— M5-BOUNDARY-REVIEW-v1.md L179

### D3.3 Frozen Spec 对应章节及原文(Contract v0.2 冻结条款)

§0.1 冻结内容 ① + §1.2a(DEC-030 Decision 1 + DEC-031 终局确认):

> 「跨系统身份键 = `SHA256(original source bytes)`,**64 字符小写 hex**;**键名 = `source_content_sha256`**」;「`source_version_id` 词面**专用化为 V3 内部 UUID FK**」。

同文件命名对照表(producer 域,L128):

> | producer IR 文件级 sha | `source_sha256` | 不变(producer 域) | sha256 hex | 映射(与接口键同值) |

且 L100:「IR 侧有 `source_sha256`(源 md 原始字节 SHA-256)……与接口键 `source_content_sha256` **同值映射**,IR 侧无同名关联键。」——**冻结契约故意让两个名字在各自域并存**。

### D3.4 Contract 对应章节及原文(同文件,实现边界面)

§5.6.2 验证行:

> `IR identity(IR.source_content_sha256 == Manifest.source_content_sha256)`

注意:**Contract 正文此处自己就写 `IR.source_content_sha256`**,而 producer IR 文件里的实际字段是 `source_sha256`(§1.1 L100 自己承认)。Contract 对 **V3 内部 dataclass 字段名**零规定(无 Python 签名层)。

### D3.5 Design 对应章节及原文(Design v1.1 §4.4,自述冻结文本)

> ```
> 文件: backend/scripts/preprocessing_consumer/identity/ir_identity_reader.py
> @dataclass(frozen=True)
> class IRIdentity:
>     source_sha256: str | None           # 64-char lowercase hex, or None if IR absent
> def read_ir_identity(ir_path: Path) -> IRIdentity:
>     输出: IRIdentity(source_sha256=...)
> ```

### D3.6 当前 `cc12d79` 实现

`backend/app/core/ir_identity.py`(sha256 前缀 `f960b513a935c8ca`,6430B,v1.2.0):

- L47-49:`@dataclass(frozen=True) class IRIdentity: source_content_sha256: str | None`(**实现用接口键名**);
- L90/L108:batch 条目实际读取的 producer 字段 = `ir_data.get("source_sha256")`(**producer 域名字原样**);
- L127-129:单文档 IR 兼容双名(`source_content_sha256` 优先,回退 `source_sha256`);
- L133-153:`read_ir_identity(ir_path, source_file=None, source_sha=None)`(Phase 2.5 locator closure 扩展了签名,与本 D 项正交);
- runner_b2 L100:`ir_sha = ir_id.source_content_sha256`(下游消费现行字段名)。

### D3.7 对应测试

`backend/tests/test_ir_identity.py`:全文件断言均钉 `result.source_content_sha256`(L26/L39-41/L48/L53/L58/L65/L114/L140 等);L62-65 注明「Design v1.1 §4.4: IR missing → source_sha256=None,不抛异常」——**测试注释引用的是行为条款,断言钉的是实现字段名**。另有 `test_adversarial_ir_identity.py` + Phase 2.5 新增 locator 测试(sha-first/path fallback)不受字段名影响。

### D3.8 具体冲突 / 歧义是什么

V3 内部产物 `IRIdentity` 的**字段名**,Design 钉 `source_sha256`(镜像它实际读取的 producer 字段),实现用 `source_content_sha256`(镜像 Contract §5.6.2 正文的表述与跨系统接口键名)。**值、算法、格式、行为零分歧**(64 小写 hex,producer 域字段名两边都原样读 `source_sha256`)。歧义本质:**Contract 的双名域分离(接口键 vs producer 域)延伸到 V3 内部 dataclass 时,该内部字段算哪一侧的面**,冻结契约未定义,Design 与实现各自选了一边。

### D3.9 为什么属于 Owner Decision,而不是普通 implementation defect

- 身份键命名属**已裁六项之一**(`source_content_sha256` = 跨系统接口键,DEC-030/031 终局)。DSH 若自行判定"内部字段应叫什么",等于在已裁命名域与 Design 自述冻结之间**自行解释权威**——正是铁律禁止的 self-adjudication;且重开命名裁决本身违规。
- Contract 对该内部字段零规定 → 无违反冻结对象可言 → 不是普通 defect;而 Design §4.7 把任何签名改动系于 Owner 令。
- 影响面为零行为、纯命名 → 恰因如此更无"紧急修复"通道可走,只能由权威侧一次性收口。

### D3.10 合理解释(全部列出)

- **解释 A(追认实现)**:`IRIdentity` 是 V3 内部对账产物,其语义 = 「与 Manifest 侧对账用的接口键值」,用 `source_content_sha256` 与 Contract §5.6.2 正文(`IR.source_content_sha256`)、M4/M5 下游键名一致,读者无须跨文档换算;Design v1.2 改字段名。
- **解释 B(回到 Design)**:字段值物理上提取自 producer IR 的 `source_sha256`,命名镜像来源字段可避免"以为 IR 里真有这个键"的误读(producer 域名字已由 Contract 冻结为不变);改实现 + 测试(约数十处断言)+ runner_b2 L100 一行。

### D3.11 每种解释的影响

| 影响面 | 解释 A | 解释 B |
|---|---|---|
| Consumer Boundary | 无变化 | 无行为变化;M3+测试+runner 一处调用点改名 |
| fail-closed | 不变 | 不变 |
| 数据模型 | 无(不涉 manifest/IR/DB;producer 域 `source_sha256` 两种方案下都原样) | 同左 |
| 后续阶段 | 下游统一以接口键名阅读,跨文档一致性高 | 与 producer 字段名一致,溯源直读 |
| 已裁六项 | 两者均不重开(接口键名与 producer 域名均不动) | 同左 |

### D3.12 Guardian conformance analysis

两种命名**均符合** Frozen Contract(§0.1 ①/§1.2a 的双名域分离在两种方案下都完整);均不触碰 Producer 与冻结对象;行为面(15 项 locator 对抗 + 活体 71/88)与字段名完全解耦。DSH 陈述符合性,不选择。

### D3.13 Owner must decide

> **Owner must decide:D3 —— V3 内部 `IRIdentity` 字段名以哪份为准:解释 A(维持实现 `source_content_sha256`,Design v1.2 改写 §4.4)还是解释 B(按 Design v1.1 §4.4 改实现为 `source_sha256`,同步改测试与 runner_b2 L100);并确认无论选哪边,producer 域字段名 `source_sha256` 与跨系统接口键 `source_content_sha256` 的双名域分离(已裁六项之一)保持不动。**

---

## D4 — M5 Identity Gate 的接口面(路径/函数名/`gate` 字段/`mismatches` 类型)+ design §4.6 文本面

### D4.1 首次发现来源

同 D2:M5-BOUNDARY-REVIEW-v1.md §10,登记表第 D4 行(DEC-042 轮)。该行当时即将 D4 拆为两半并注明:语义偏离(VERIFIED+PENDING→BLOCK)「与 **Owner DEC-042 Truth Table 一致**」,接口偏离「待收口」。DEC-044 轮(CLOSURE-REVIEW L122)定型为「**OPEN(部分已裁)**:语义部分 = Owner Truth Table 生效,design 文本被超越;接口面待 Claude 与 design v1.2 收口」;DEC-048 维持(`identity_gate.py` 锚 `8a5d267e285800f0`/6163B)。

### D4.2 原始 observation / discrepancy(原文照录)

> | D4 | M5 接口+语义 | `evaluate_identity` @ `scripts/preprocessing_consumer/identity/identity_gate.py`;输出无 `gate` 字段;`mismatches: list`;**VERIFIED+PENDING → 进入 Gate/Admission + 语义层标记 PENDING**(§1.3/§3.1 F4·F5·F13/§4.6) | `evaluate_identity_gate` @ `app/core/identity_gate.py`;输出**增 `gate: PASS|BLOCK` 字段**;`mismatches: tuple`;**VERIFIED+PENDING → BLOCK** | 语义偏离与 **Owner DEC-042 Truth Table 一致**(实现 docstring 已明注「Owner 指令优先于 Design v1.1 §4.6」);接口偏离(路径/函数名/字段)待收口 |
> —— M5-BOUNDARY-REVIEW-v1.md L180

### D4.3 Frozen Spec 对应章节及原文(Contract v0.2 冻结条款)

§1.6(16 份 Semantic Pending,DECISION):

> 「接口面 87 中 **16 份**……**Identity Available / Semantic Pending**……V3 应完成身份对账、暂不语义消费、标记 pending」;并注「接口面是否设呈现字段 = 未裁(OQ-21 / DSH 同)」。

§5.6.2:

> 失败:`fail-closed(任何关键验证失败 → 阻断消费,不得继续向下游)`;成功:`进入既有 V3 Gate / Admission 链`。验证清单含 `IR identity(IR.source_content_sha256 == Manifest.source_content_sha256)`。

**Contract 对 M5 Python 签名零规定**(同 D2.4 grep 证据;`evaluate_identity`/`IdentityGateDecision`/`gate` 字段均无命中)。**注意一处真实张力(取证陈述,非裁决)**:Contract §1.6 的「标记 pending」与 Owner Truth Table 的「VERIFIED+PENDING→BLOCK」在"BLOCK 的文档无法落入任何 Admission 记录、因而无处被标记"这一点上**尚未被任何权威文本调和**;冻结契约自身把呈现字段挂为 **OQ-21 未裁**。

### D4.4 Contract 对应章节及原文(Owner Truth Table,历轮指令)

DEC-042(Owner 聊天指令,ODR 照录):VERIFIED+AVAILABLE→PASS;**VERIFIED+PENDING→BLOCK(最高优先级)**;VERIFIED+None→BLOCK;FAILED any→BLOCK;INVALID any→BLOCK。DEC-044/045/046/047/048 各轮指令均再确认,且 DEC-048 指令⑥明确「不自行解决 authority conflict」。

### D4.5 Design 对应章节及原文(Design v1.1 §4.6 + §1.2/§1.3/§3.1 F13,自述冻结文本)

§4.6:

> ```
> 文件: backend/scripts/preprocessing_consumer/identity/identity_gate.py
> class IdentityGateDecision:
>     identity_state: str; semantic_state: str | None; reason: str; mismatches: list[str]
> def evaluate_identity(verification) -> IdentityGateDecision: ...
> 下游动作:
>   - identity_state="FAILED" → 阻断消费,不创建 Document/SourceVersion/Candidate
>   - identity_state="VERIFIED" → 进入既有 Gate/Admission 链
>     - semantic_state="PENDING" → 语义层标记 PENDING(OQ-21)
> ```

§1.3 组合矩阵:`VERIFIED×PENDING → 进入 Gate/Admission,语义层标记 PENDING`。§3.1 F13(stale IR):「动作:放行,语义层标记 PENDING」。

### D4.6 当前 `cc12d79` 实现

`backend/app/core/identity_gate.py`(sha256 前缀 `8a5d267e285800f0`,6163B,v1.2.0):

- L7-18:docstring 内嵌 Owner Truth Table 全表,明注「Owner 指令,**超越 Design v1.1 §4.6**」;核心不变量「VERIFIED + PENDING = BLOCK(最高优先级)」;
- L59-65:`IdentityGateDecision(gate: "PASS"|"BLOCK", identity_state, semantic_state, reason, mismatches: tuple[str,...])`——**增 `gate` 字段;`mismatches` 为 tuple**;
- L68:`evaluate_identity_gate(verification)` @ `app/core/`,非 Design 的 `evaluate_identity` @ `scripts/…/identity/`;
- L42-56:值域白名单 + `_normalize_str` str-subclass 防御(v1.2.0,DEC-048 审过;残留 = D-048-1,另行挂账,不并入本 D 项);
- L145-149:PENDING → BLOCK(REASON_SEMANTIC_PENDING)。

### D4.7 对应测试

`backend/tests/test_identity_gate.py`:L36/46/55/62/70/82/90 断言均经 `decision.gate == GATE_PASS/GATE_BLOCK`(**钉 `gate` 字段**);L42-82 一组 `test_verified_pending*` **钉 VERIFIED+PENDING→BLOCK**(= Owner Truth Table 行为);L103-106 `test_mismatches_is_tuple` **钉 tuple**;L120 钉 `hasattr(decision, "mismatches")`。另有 `test_adversarial_m5_round1/2.py`(Claude 侧)与 DSH DEC-048 攻击电池(EvilEq/EvilStrOnly/EvilRaise 等)对同一行为面交叉验证。

### D4.8 具体冲突 / 歧义是什么

拆两层:

- **语义层(已裁,文本未收口)**:VERIFIED+PENDING 的处置,Design §1.2/§1.3/§3.1 F13/§4.6 = 「放行 + 标记 PENDING」,Owner Truth Table = 「BLOCK」。Owner 已裁(Truth Table 生效,实现与测试均按此);但 **Design v1.1 的四处文本仍是旧语义,v1.2 修订令未下达**;且冻结 Contract §1.6「标记 pending」与 OQ-21(呈现字段)在 BLOCK 语义下如何呈现**没有任何权威文本给出答案**——"被 BLOCK 的 16 份在接口上以什么形态呈现为 pending"至今未裁。
- **接口层(未裁)**:① 模块路径 `app/core/identity_gate.py` ≠ Design `scripts/preprocessing_consumer/identity/identity_gate.py`;② 函数名 `evaluate_identity_gate` ≠ `evaluate_identity`;③ 输出增 `gate: PASS|BLOCK` 字段(Design 无);④ `mismatches: tuple` ≠ Design `list`。接口层与行为层解耦:四项偏离均不改变任何 Truth Table 结果;但③已产生实现耦合(runner_b2 L113 读 `decision.gate`)。

### D4.9 为什么属于 Owner Decision,而不是普通 implementation defect

- 语义层虽已裁,但**裁决的文本落地(Design v1.2)与 Contract §1.6/OQ-21 的调和**是冻结契约自身的开放项——OQ-21 挂在 Owner 名下(Contract L205),DSH 无权代答;BLOCK 语义下"标记 pending"载体为空,这是契约文本与 Owner 指令之间仅存的 **authority 张力**,按 DEC-048 指令⑥明令不得自行解决。
- 接口层四偏离:Design §4.7 自述冻结 + 「任何修改须 Owner 另行下令」;改哪边(V3 文档 vs V3 代码)均出 DSH 权限;且 DSH 纪律 = 不写 Consumer 代码。
- 现行行为已被 DEC-044/048 全链实测 fail-closed 安全 → 无缺陷修复通道的适用性。

### D4.10 合理解释(全部列出)

- **解释 A(追认实现 + Design v1.2 全面改写)**:Design §1.2/§1.3/§3.1 F13/§4.6 按 Owner Truth Table 与现行接口重写(路径/函数名/`gate` 字段/tuple/PENDING→BLOCK);`gate` 字段作为显式决策位被下游(runner_b2 L113)消费,有实现价值。
- **解释 B(接口回到 Design,语义保留 Owner 表)**:实现改回 `evaluate_identity` @ Design 路径、去 `gate` 字段(runner 改为读 `identity_state/semantic_state` 组合)、`mismatches` 改回 `list`;语义恒为 Owner Truth Table,**Design 语义文本仍必须出 v1.2**——即 B 只解决接口层,文本修订令在两种解释下都不可避免。
- **解释 C(仅在 Owner 显式重开时存在)**:语义回到 Design「放行 + 标记 PENDING」。**当前不在桌上**——它直接推翻 Owner 已裁 Truth Table(DEC-042 至 DEC-048 六轮再确认),除非 Owner 明示重开,任何一方不得提案执行。列出仅为完备性。

### D4.11 每种解释的影响

| 影响面 | 解释 A | 解释 B | 解释 C(须 Owner 显式重开) |
|---|---|---|---|
| Consumer Boundary | 无行为变化;docs-only | 无行为变化;M5+测试+runner 调用点重构 | **行为推翻**:17 份 PENDING/FAILED 文档中 16 份将进入 Gate/Admission 链 —— 须重跑 DEC-047/048 全部 BLOCK 证据 |
| fail-closed | 不变 | 不变 | **弱化方向**(PENDING 不再阻断),与 §5.6.2 的读法冲突须一并裁 |
| 数据模型 | 无 | 无 | Admission 面将出现 semantic=PENDING 记录 → 与 OQ-21 呈现字段、16 份重跑血统(§1.6 约束⑦)强耦合 |
| 后续阶段 | v1.2 文本一次到位,OQ-21 仍须单独裁 | v1.2 文本仍须出;`gate` 字段移除 = 下游判定位重构 | 重新打开一串已收口问题 |

### D4.12 Guardian conformance analysis

解释 A/B 均满足 Contract §5.6.2 与 Owner Truth Table(行为不动);A 为 V3 docs-only,B 为 V3 代码重构,两者均不触碰 Producer/冻结对象。**无论 A/B,以下三件事都必须由同一收口令或后续令覆盖,否则 D4 无法真正关闭**:① Design v1.1 四处旧语义文本的 v1.2 修订;② OQ-21(VERIFIED+PENDING 被 BLOCK 后的呈现字段/标记载体)的裁决;③ Contract §1.6「标记 pending」措辞在 BLOCK 语义下的解释归属(契约文本本身是否需要随 v0.2→v0.3 演进,属 Owner 冻结对象管理权)。DSH 只登记,不选择。

### D4.13 Owner must decide

> **Owner must decide:D4 —— (i) 接口面收口方向:解释 A(Design v1.2 追认实现:路径 `app/core/`、`evaluate_identity_gate`、`gate` 字段、`mismatches: tuple`)还是解释 B(实现回到 Design §4.6 接口,语义保留 Owner Truth Table);(ii) Design v1.1 §1.2/§1.3/§3.1 F13/§4.6 旧语义文本的 v1.2 修订令与责任归属;(iii) OQ-21:被 BLOCK 的 VERIFIED+PENDING 文档(真实语料 16 份)在接口上以何种载体呈现 pending(含 Contract §1.6「标记 pending」措辞的解释归属)。解释 C 仅在 Owner 显式重开 Truth Table 时才进入讨论。**

---

## §5 汇总表

| 项 | 争议一句话 | 与 Frozen Contract 的关系 | 与 Design v1.1 的关系 | 行为/fail-closed | 待裁内容 |
|---|---|---|---|---|---|
| **D2** | M2 接口形状(bytes 保留与否 + 异常类型 + 函数名/路径) | Contract **零规定**该签名;能力条款(§0.1⑥/§2.3)两边均满足 | §4.3 自述冻结,实现四重偏离 | 无分歧,fail-closed 实测成立 | A 追认 / B 改回 / 混合变体 |
| **D3** | M3 内部 dataclass 字段名 | Contract 双名域分离(§1.2a + L128),对内部字段**零规定**;§5.6.2 正文自写 `IR.source_content_sha256` | §4.4 钉 `source_sha256` | 无分歧 | A 追认 / B 改回 |
| **D4** | M5 接口面(路径/函数名/`gate`/tuple)+ Design 旧语义文本 + OQ-21 | Contract §5.6.2 满足;§1.6「标记 pending」+ OQ-21 与 BLOCK 语义的调和**未裁** | §1.2/§1.3/§3.1 F13/§4.6 语义已被 Owner Truth Table 超越,文本待 v1.2;接口四偏离 | 语义已裁;接口无行为影响 | (i) A/B 接口方向 (ii) v1.2 修订令 (iii) OQ-21 |

**三项全部证据充分,无 "Insufficient evidence to reconstruct" 项。**

## §6 纪律执行记录(本轮)

- 全程只读:V3 仓零写入(仅读文件 + `git ls-files`/`rev-parse`/`log` 只读查询);Frozen Contract 未动(sha256 亲验 MATCH);Producer 数据未动;Papers 侧仅 docs-only 登记。
- 未修改任何代码、未修改 Frozen Spec、未自行选择 A/B、未以测试通过充当裁决、未以 D 项名称代替问题定义。
- 权威冲突(Design 自述冻结 vs Contract 零规定 vs Owner Truth Table)按 DEC-048 指令⑥原样上报,零 self-adjudication。
- 证据来源分层标注:Owner 指令 / Frozen Contract 原文 / Design v1.1 原文 / cc12d79 实现(hash 锚)/ 测试断言(行号)/ 历轮登记(报告路径 + 行号)。
