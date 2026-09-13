# -*- coding: utf-8 -*-
"""
BUG-11 回归钉 — recover_images 扫描范围 = "排除派生目录,其余顶层一律为源"(单一来源)。

旧缺陷:SCAN_DIRS 硬编码 ["高一","高二","高三","未分类"],重归类迁出的
高考真题/合格考/会考/竞赛自招/其他汇编/学业水平考试 六个源目录完全不可见,
缺图文件永远无法增量修复(目录布局变更 → 白名单静默失配)。

契约:
  t1 新增源顶层目录自动纳入(白名单回退即咬合)
  t2 派生/输出目录全部排除(_imgs/.cache/auto-annotated-*/reslice*)
  t3 嵌套 _imgs 与非 md 文件不入扫描;结果确定性排序
  t4 is_source_top_dir 纯函数逐条断言(排除表双向)
  t5 真实语料冒烟:六个重归类目录的 md 确实进入扫描结果(无语料环境则 skip)
"""
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import recover_images as ri


def _mk(root: Path, rel: str):
    p = root / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text("x", encoding="utf-8")
    return p


def test_new_source_topdir_is_scanned(workdir):
    """t1:白名单时代不存在的目录必须自动可见。"""
    _mk(workdir, "高一/a.md")
    _mk(workdir, "高考真题/b.md")
    _mk(workdir, "全新源目录2026/c.md")          # 白名单回退时必然漏掉
    _mk(workdir, "学业水平考试/deep/nest/d.md")  # 深层嵌套也要可见
    got = [Path(p).relative_to(workdir).as_posix() for p in ri.scan_md_files(str(workdir))]
    assert set(got) == {"高一/a.md", "高考真题/b.md",
                        "全新源目录2026/c.md", "学业水平考试/deep/nest/d.md"}
    assert got == sorted(got), "扫描结果必须确定性排序"


def test_derived_dirs_excluded(workdir):
    """t2:派生/输出目录一个都不能进扫描(防止对产物就地重写)。"""
    derived = [
        "_imgs/某名/x.md",
        ".cache/x.md",
        "auto-annotated-v3/x.md",
        "auto-annotated-v6/x.md",
        "reslice-pac/x.md",
        "reslice-batch-C/x.md",
        "resliced-pilot/x.md",
    ]
    for rel in derived:
        _mk(workdir, rel)
    _mk(workdir, "高一/keep.md")
    got = [Path(p).relative_to(workdir).as_posix() for p in ri.scan_md_files(str(workdir))]
    assert got == ["高一/keep.md"]


def test_non_md_and_nested_imgs_skipped(workdir):
    """t3:非 md 不扫;源目录内部嵌套的 _imgs 不扫。"""
    _mk(workdir, "高一/a.md")
    _mk(workdir, "高一/readme.txt")
    _mk(workdir, "高一/_imgs/sub/cached.md")
    _mk(workdir, "高一/nested/_imgs/inner.md")
    _mk(workdir, "高一/nested/real.md")
    got = [Path(p).relative_to(workdir).as_posix() for p in ri.scan_md_files(str(workdir))]
    assert got == ["高一/a.md", "高一/nested/real.md"]


def test_is_source_top_dir_table():
    """t4:纯函数排除表双向断言(排除项漏一个或源项误伤一个都咬)。"""
    for name in ["高一", "高二", "高三", "未分类", "高考真题", "合格考",
                 "会考", "竞赛自招", "其他汇编", "学业水平考试", "任意新目录"]:
        assert ri.is_source_top_dir(name), name
    for name in ["_imgs", ".cache", "auto-annotated-v3", "auto-annotated-v6",
                 "reslice-pac", "reslice-batch-C", "resliced-pilot"]:
        assert not ri.is_source_top_dir(name), name


@pytest.mark.skipif(not Path(ri.OCR_ROOT).is_dir(), reason="corpus 语料目录不存在(CI)")
def test_real_corpus_reclassify_dirs_visible():
    """t5:真实语料 — BUG-11 的六个重归类目录必须出现在扫描结果里。"""
    scanned = ri.scan_md_files()
    assert scanned, "真实语料扫描结果为空,异常"
    new_dirs = ["高考真题", "合格考", "会考", "竞赛自招", "其他汇编", "学业水平考试"]
    for d in new_dirs:
        marker = str(Path(ri.OCR_ROOT) / d)
        assert any(p.startswith(marker) for p in scanned), f"重归类目录仍不可见: {d}"
    # 旧白名单口径必须是新口径的真子集(修复=扩视野,不是挪视野)
    old = {"高一", "高二", "高三", "未分类"}
    old_set = {p for p in scanned if Path(p).relative_to(ri.OCR_ROOT).parts[0] in old}
    assert old_set and old_set < set(scanned)
