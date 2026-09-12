# -*- coding: utf-8 -*-
"""rel_out 路径归属契约(固化 R24-A2)。"""
from pathlib import Path

import reslice_pipeline as rp


def test_subpath_resolves():
    root = Path("D:/x/Ocr-markdown")
    f = root / "高一" / "a.md"
    assert rp.rel_out(f, root) == Path("高一/a.md")


def test_prefix_confusion_does_not_crash():
    """R24-A2:'Ocr-markdown2' 误判为子路径 → relative_to 抛 ValueError → 崩整批。
    rel_out 必须回落到 basename 而非抛异常。"""
    root = Path("D:/x/Ocr-markdown")
    f = Path("D:/x/Ocr-markdown2/fake.md")
    assert str(f).startswith(str(root))                 # 旧逻辑的陷阱前提
    assert rp.rel_out(f, root) == Path("fake.md")      # 不崩,回落 basename


def test_absolute_unrelated_falls_back():
    root = Path("D:/x/Ocr-markdown")
    assert rp.rel_out(Path("E:/other/b.md"), root) == Path("b.md")
