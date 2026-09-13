# -*- coding: utf-8 -*-
"""R66:BUG-14-DATA D5-A 跑步机切断机制钉(R-OHM-1)。

用户 R65 裁定:只修重复处理/重复回流机制 + 修复前冻结快照;
不碰语义去重、不碰 canonical identity、不碰 BUG-14-CHAIN。

集成测试跑的是**真实 batch_convert_pdf.main()**,仅 stub 掉 process_pdf
(零 OCR API、零网络);skip 判定、清单载入/记账、fail-closed 中止全部是真代码。

  test_r66_t1  EXISTS 既有行为原样保留(>100B 静默 skip;<=100B 重跑)
  test_r66_t2  跑步机切断(核心):OCR→记账→reclassify 搬移→再跑 main()
               → MANIFEST_DONE skip,不再二次 OCR,未分类零回流
  test_r66_t3  SOURCE_CHANGED:size 变 / size 同而 sha 变 → 必须重 OCR(禁假 skip)
  test_r66_t4  记录输出丢失不自动重跑(重跑权在人:删除清单记录 = 显式重跑授权)
  test_r66_t5  清单损坏 fail-closed:main() SystemExit(2),FATAL 入日志,OCR 零调用
  test_r66_t6  append 校验 fail-closed:坏记录不落盘,文件字节不变
  test_r66_t7  load:同键 last-wins;反斜杠键归一匹配(F-r64-1 教训回归钉)
  test_r66_t8  decide_skip 原因电池(NO_MANIFEST_ENTRY / SOURCE_UNVERIFIABLE)
  test_r66_t9  runner 源码锚:R66 接线原文 + process_pdf 既有 skip-check 保留 +
               R-OHM-1 登记在册
  test_r66_t10 快照武器阳性控制:字节篡改必入 changed、幽灵入 missing、新文件入 new
"""
import importlib
import importlib.util
import json
import os
import re
import shutil
import sys
import types
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "ocr_service"))

import output_manifest as om  # noqa: E402

RUNNER_SRC = (ROOT / "ocr_service" / "batch_convert_pdf.py").read_text(encoding="utf-8")
REGISTRY = (ROOT / "governance" / "rule_registry.md").read_text(encoding="utf-8")

PDF_NAME = "2012-2021高考真题历史汇编：跑步机测试（教师版）(1).pdf"
MD_NAME = "2012-2021高考真题历史汇编：跑步机测试（教师版）(1).md"
OUT_REL = "未分类/历史/" + MD_NAME


def _stub_optional_deps():
    """CI 仅装 pytest:requests/urllib3 缺席时注入 import 级 stub(测试禁网)。"""
    if importlib.util.find_spec("requests") is None:
        req = types.ModuleType("requests")

        class _Session:
            verify = True
            proxies = {}

            def get(self, *a, **k):
                raise RuntimeError("测试禁网")

            def post(self, *a, **k):
                raise RuntimeError("测试禁网")

        req.Session = _Session
        sys.modules["requests"] = req
    if importlib.util.find_spec("urllib3") is None:
        u3 = types.ModuleType("urllib3")

        class _Exceptions:
            class InsecureRequestWarning(Warning):
                pass

        u3.exceptions = _Exceptions
        u3.disable_warnings = lambda *a, **k: None
        sys.modules["urllib3"] = u3


class Harness:
    """真实 main() + 合成根目录;process_pdf 为记账 stub(写真实 md 文件)。"""

    def __init__(self, workdir, monkeypatch):
        monkeypatch.setenv("OCR_API_TOKEN", "test-token-not-real")
        _stub_optional_deps()
        self.mod = importlib.import_module("batch_convert_pdf")
        self.pdf_root = workdir / "maintainess" / "PDF"
        self.out_root = workdir / "Ocr-markdown"
        self.pdf_root.mkdir(parents=True)
        self.pdf = self.pdf_root / PDF_NAME
        self.write_pdf(b"%PDF-1.4 fake source v1 " + b"a" * 50)
        self.manifest = workdir / "ocr_output_manifest.jsonl"
        self.logfile = workdir / "ocr_batch_log.txt"
        self.calls = []
        monkeypatch.setattr(self.mod, "PDF_ROOT", str(self.pdf_root))
        monkeypatch.setattr(self.mod, "OUTPUT_ROOT", str(self.out_root))
        monkeypatch.setattr(self.mod, "LOG_FILE", str(self.logfile))
        monkeypatch.setattr(self.mod, "PAGE_USAGE_FILE",
                            str(workdir / "ocr_page_usage.json"))
        monkeypatch.setattr(self.mod, "MANIFEST_FILE", str(self.manifest))
        monkeypatch.setattr(self.mod.time, "sleep", lambda s: None)
        calls = self.calls

        def fake_process_pdf(file_path, output_dir, original_filename,
                             page_usage):
            calls.append(original_filename)
            os.makedirs(output_dir, exist_ok=True)
            stem = re.sub(r'[<>:"/\\|?*]', '_',
                          os.path.splitext(original_filename)[0])
            with open(os.path.join(output_dir, f"{stem}.md"), "w",
                      encoding="utf-8") as f:
                f.write("# OCR 输出\n" + "正文内容。" * 30 + "\n")
            return True, 7

        monkeypatch.setattr(self.mod, "process_pdf", fake_process_pdf)

    def write_pdf(self, data):
        self.pdf.write_bytes(data)

    def run_main(self):
        self.mod.main()

    def log_text(self):
        if not self.logfile.exists():
            return ""
        return self.logfile.read_text(encoding="utf-8")

    def manifest_lines(self):
        if not self.manifest.exists():
            return []
        return [ln for ln in
                self.manifest.read_text(encoding="utf-8").splitlines()
                if ln.strip()]


# ---------------------------------------------------------------------------
# 集成钉(真实 main(),零 API)
# ---------------------------------------------------------------------------
def test_r66_t1_EXISTS既有行为保留(monkeypatch, workdir):
    h = Harness(workdir, monkeypatch)
    h.run_main()
    assert h.calls == [PDF_NAME]
    assert (h.out_root / "未分类" / "历史" / MD_NAME).exists()
    n_decide = h.log_text().count("[DECIDE:")
    assert n_decide == 1, "首轮唯一决策(NO_MANIFEST_ENTRY)必须留证"
    h.run_main()  # 输出仍在原位 → 既有 EXISTS 语义,静默 skip
    assert h.calls == [PDF_NAME], "EXISTS 路径不得重新 OCR"
    assert h.log_text().count("[DECIDE:") == n_decide, \
        "EXISTS 必须保持既有静默行为(第二轮不新增决策日志)"


def test_r66_t2_跑步机切断(monkeypatch, workdir):
    """核心机制钉:reclassify 搬移后,第二轮 main() 不再重 OCR、未分类零回流。"""
    h = Harness(workdir, monkeypatch)
    h.run_main()
    assert h.calls == [PDF_NAME]
    src_md = h.out_root / "未分类" / "历史" / MD_NAME
    assert src_md.exists(), "前置:第一轮产出落在 未分类/历史"
    assert len(h.manifest_lines()) == 1, "前置:成功写出即记账"

    dst_dir = h.out_root / "高考真题" / "历史"
    dst_dir.mkdir(parents=True)
    shutil.move(str(src_md), str(dst_dir / MD_NAME))  # 模拟 reclassify --apply

    h.run_main()
    assert h.calls == [PDF_NAME], "跑步机未切断:同一 PDF 被二次 OCR"
    assert not src_md.exists(), "跑步机复活:未分类出现回流文件"
    assert (dst_dir / MD_NAME).exists(), "搬移后的产出不得被动"
    assert len(h.manifest_lines()) == 1, "skip 不得追加清单记录"
    assert "[DECIDE:MANIFEST_DONE]" in h.log_text(), "skip 必须显式留证"
    assert "missing-or-moved" in h.log_text(), "记录输出现状必须入日志留证"


def test_r66_t3_SOURCE_CHANGED必须重OCR(monkeypatch, workdir):
    h = Harness(workdir, monkeypatch)
    h.run_main()
    assert h.calls == [PDF_NAME]
    src_md = h.out_root / "未分类" / "历史" / MD_NAME

    # 期望输出不在位(搬移态)+ size 变化 → 源已换,必须重跑
    src_md.unlink()
    h.write_pdf(b"%PDF-1.4 fake source v2 " + b"b" * 90)
    h.run_main()
    assert h.calls == [PDF_NAME, PDF_NAME], "size 变化必须重 OCR"
    assert "[DECIDE:SOURCE_CHANGED]" in h.log_text()

    # size 相同、内容不同(sha 层身份)→ 同样必须重跑
    src_md.unlink()
    v3 = b"%PDF-1.4 fake source v3 " + b"c" * 90
    assert len(v3) == 114, "前置:size 必须与 v2 相同"
    h.write_pdf(v3)
    h.run_main()
    assert h.calls == [PDF_NAME] * 3, "sha 不一致(size 相同)必须重 OCR"
    assert h.log_text().count("[DECIDE:SOURCE_CHANGED]") == 2


def test_r66_t4_输出丢失不自动重跑(monkeypatch, workdir):
    """设计裁定钉:输出被搬移/丢失后的重跑权在人(删清单记录),不在 runner。"""
    h = Harness(workdir, monkeypatch)
    h.run_main()
    src_md = h.out_root / "未分类" / "历史" / MD_NAME
    src_md.unlink()
    h.run_main()
    assert h.calls == [PDF_NAME], "输出丢失不得触发自动重跑(auto-fix 禁)"
    assert "[DECIDE:MANIFEST_DONE]" in h.log_text()
    assert "missing-or-moved" in h.log_text()

    h.manifest.unlink()  # 操作者显式清除清单 = 重跑授权
    h.run_main()
    assert h.calls == [PDF_NAME, PDF_NAME], "显式清清单后必须恢复可重跑"


# ---------------------------------------------------------------------------
# fail-closed 钉
# ---------------------------------------------------------------------------
def test_r66_t5_清单损坏中止(monkeypatch, workdir):
    h = Harness(workdir, monkeypatch)
    good = json.dumps({
        "source_rel": "X.pdf", "source_size": 1, "source_sha256": "a" * 64,
        "output_rel": "未分类/历史/X.md", "written_at": "2026-09-13 00:00:00",
        "pages": 1}, ensure_ascii=False)
    h.manifest.write_text(good + "\nnot-json-line\n", encoding="utf-8")
    with pytest.raises(SystemExit) as ei:
        h.run_main()
    assert ei.value.code == 2
    assert h.calls == [], "清单损坏时必须零 OCR(fail-closed,禁降级重跑)"
    assert "FATAL" in h.log_text() and "输出清单损坏" in h.log_text()


def test_r66_t6_坏记录不落盘(workdir):
    mf = workdir / "m.jsonl"
    before = b'{"good": 1}\n'
    mf.write_bytes(before)
    bad = {"source_rel": "A.pdf"}  # 缺键
    with pytest.raises(om.ManifestError):
        om.append_entry(str(mf), bad)
    assert mf.read_bytes() == before, "坏记录绝不得落盘"


def test_r66_t7_load语义(workdir):
    mf = workdir / "m.jsonl"
    assert om.load_manifest(str(mf)) == {}, "缺失文件 = 空清单(首次运行)"

    def entry(source_rel, size):
        return json.dumps({
            "source_rel": source_rel, "source_size": size,
            "source_sha256": "b" * 64, "output_rel": "未分类/历史/X.md",
            "written_at": "2026-09-13 00:00:00", "pages": 1},
            ensure_ascii=False)
    mf.write_text(entry("sub\\A.pdf", 1) + "\n" + entry("sub/A.pdf", 2) + "\n",
                  encoding="utf-8")
    m = om.load_manifest(str(mf))
    assert list(m) == ["sub/A.pdf"], "反斜杠键必须归一(F-r64-1 教训)"
    assert m["sub/A.pdf"]["source_size"] == 2, "同键必须 last-wins"


def test_r66_t8_decide_skip原因电池(workdir):
    pdf_root = workdir / "pdfs"
    pdf_root.mkdir()
    pdf = pdf_root / "A.pdf"
    pdf.write_bytes(b"%PDF-fake-1234")
    out_root = workdir / "out"
    out_root.mkdir()
    out_md = out_root / "未分类" / "历史" / "A.md"
    kw = dict(output_md=str(out_md), source_pdf=str(pdf),
              pdf_root=str(pdf_root), output_root=str(out_root))

    skip, reason, _ = om.decide_skip(manifest={}, **kw)
    assert (skip, reason) == (False, "NO_MANIFEST_ENTRY")

    entry = {"source_rel": "A.pdf", "source_size": len(b"%PDF-fake-1234"),
             "source_sha256": om.file_sha256(str(pdf)),
             "output_rel": "未分类/历史/A.md",
             "written_at": "2026-09-13 00:00:00", "pages": 1}
    skip, reason, detail = om.decide_skip(manifest={"A.pdf": entry}, **kw)
    assert (skip, reason) == (True, "MANIFEST_DONE")
    assert detail["recorded_output_status"] == "missing-or-moved"

    pdf.unlink()
    skip, reason, _ = om.decide_skip(manifest={"A.pdf": entry}, **kw)
    assert (skip, reason) == (False, "SOURCE_UNVERIFIABLE"), \
        "source 不可验证时禁猜,放行并显式留因"


# ---------------------------------------------------------------------------
# 源码锚 + 登记册双向钉
# ---------------------------------------------------------------------------
def test_r66_t9_runner接线锚():
    for anchor in [
        "from output_manifest import (ManifestError, append_entry, decide_skip,",
        r'MANIFEST_FILE = r"D:\Project\Papers\data\ocr_output_manifest.jsonl"',
        "skip_now, skip_reason, skip_detail = decide_skip(",
        "[FATAL] 输出清单损坏,拒绝继续(R-OHM-1 fail-closed)",
        "[FATAL] 输出清单写入失败,拒绝静默继续(R-OHM-1)",
        "append_entry(MANIFEST_FILE, entry)",
        # process_pdf 既有 skip-check 原样保留(R25 冻结语义,防 t8 锚漂移)
        "    if os.path.exists(output_md) and os.path.getsize(output_md) > 100:",
    ]:
        assert anchor in RUNNER_SRC, f"runner 接线锚漂移: {anchor}"
    assert "R-OHM-1" in REGISTRY, "R-OHM-1 必须登记在册(运行规则 #1)"
    assert "MANIFEST_DONE" in REGISTRY


# ---------------------------------------------------------------------------
# 快照武器阳性控制(检测器必须真的检测)
# ---------------------------------------------------------------------------
def test_r66_t10_快照武器阳性控制(workdir):
    import r66_d5a_snapshot_check as snap

    ocr = workdir / "Ocr-markdown"
    (ocr / "高一" / "数学").mkdir(parents=True)
    (ocr / "高一" / "数学" / "A.md").write_bytes("甲卷正文。\n".encode("utf-8"))
    (ocr / "高一" / "数学" / "B.md").write_bytes("乙卷正文。\n".encode("utf-8"))
    (ocr / "高一" / "数学" / "C.md").write_bytes("丙卷正文。\n".encode("utf-8"))
    env = {"R64_OCR_ROOT": str(ocr),
           "R64_PDF_ROOT": str(workdir / "pdfs"),
           "R64_DATA_DIR": str(workdir / "data"),
           "R66_BASELINE": str(workdir / "baseline.json"),
           "R66_OUT": str(workdir / "snap.json"),
           "R66_AUDIT": str(workdir / "no_audit.jsonl")}
    old = {k: os.environ.get(k) for k in env}
    os.environ.update(env)
    try:
        import r64_data_inventory as inv
        importlib.reload(inv)
        records, _ = inv.collect_inventory()
        baseline = {"records": json.loads(json.dumps(records))}
        # 篡改 B 字节 → 必须入 changed
        (ocr / "高一" / "数学" / "B.md").write_bytes(
            "乙卷正文！被篡改\n".encode("utf-8"))
        # 幽灵记录(实际不存在)→ 必须入 missing
        baseline["records"].append({"rel_path": "高一/数学/幽灵.md",
                                    "size": None, "sha256": None,
                                    "norm_sha256": None})
        # 从 baseline 摘掉 C → 必须入 new
        baseline["records"] = [r for r in baseline["records"]
                               if r["rel_path"] != "高一/数学/C.md"]
        Path(env["R66_BASELINE"]).write_text(
            json.dumps(baseline, ensure_ascii=False), encoding="utf-8")
        mod = importlib.reload(snap)
        mod.main()
        payload = json.loads(Path(env["R66_OUT"]).read_text(encoding="utf-8"))
        assert payload["counts"]["changed"] == 1
        assert payload["changed"][0]["rel_path"] == "高一/数学/B.md"
        assert payload["missing"] == ["高一/数学/幽灵.md"]
        assert payload["new"] == ["高一/数学/C.md"]
        assert len(payload["corpus_digest"]) == 64
    finally:
        for k, v in old.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v
        import r64_data_inventory as inv
        importlib.reload(inv)
        importlib.reload(snap)
