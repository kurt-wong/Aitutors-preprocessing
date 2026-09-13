# 风险登记册(risk_register.md)

**来源**:用户 R59 审核裁定(2026-09-13)——"F-r59-1 不应登记为生产 BUG(当前
没有发生),应登记为 RISK-FUTURE,类别 GOVERNANCE / Boundary;否则会污染
缺陷统计"。

**定位**:与 `bugs.md`(缺陷:已发生)分离——本册只登记**机制性未来风险**
(当前零实际损害,但存在可推演的触发路径)。每条带 触发路径 / 当前状态 /
监测手段 / 关闭条件。

---

## RISK-FUTURE-001 · Unclassified Derived Tree Admission Risk

- **类别**:GOVERNANCE / Boundary
- **来源**:BUG-11 修复(R58 排除派生目录制)的 R59 审查 F-r59-1——R58
  台账措辞"误纳派生目录的代价只是多扫"被证伪:无排除政策下 84 份派生 md
  会被 `recover_images.process_one` 真实处理(提取图片 + 就地重写 + 审计)。
- **当前状态**:风险 = 0 实际触发(`recover_images.py` 排除表覆盖现有全部
  11 个派生目录,R59 实测);这是**流程潜伏风险**,不是既成缺陷。
- **触发路径**:
  1. 新增派生目录,且名字不含 `auto-annotated` / `reslice` 前缀、不叫
     `_imgs` / `.cache`;
  2. 其内 md 恰含图片引用且 basename 命中 PDF 索引;
  3. 有人运行 `recover_images.py` → 派生树被就地重写 + 审计被污染。
- **监测手段**:`tests/test_recover_images_scan.py` t2/t4 钉住排除表;
  `r58_bug11_coverage.py` 只读视野测量。
- **缓解决策(已裁定,不改代码)**:维持排除制——改回白名单即复发 BUG-11
  (静默漏修 > 误纳处理,开放世界输入生态下前者更危险)。
- **关闭条件**:recover_images 改为显式 manifest 驱动(派生树不进扫描面),
  或排除表改为单一来源配置(与目录清单同源)。在此之前永久在册。
