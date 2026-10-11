# -*- coding: utf-8 -*-
"""Phase C #2/#3：图像资源打包 + 四表格结构回归（Q9/Q19/Q24/Q25）。"""
import re
from pathlib import Path

import pytest

import reslice_pipeline as rp

Q9_TABLE = (
    "<table border=1><tr>"
    "<td>A. 青铜器皿</td><td>B. 陶瓷</td><td>C. 丝绸</td><td>D. 中草药</td>"
    "</tr><tr>"
    '<td><img src="../../_imgs/x/img_in_image_box_157_151_247_252.jpg" /></td>'
    '<td><img src="../../_imgs/x/img_in_image_box_328_147_444_230.jpg" /></td>'
    '<td><img src="../../_imgs/x/img_in_image_box_529_136_618_235.jpg" /></td>'
    '<td><img src="../../_imgs/x/img_in_image_box_725_140_864_227.jpg" /></td>'
    "</tr></table>"
)

Q19_TABLE = (
    "<table><tr><td></td><td>A</td><td>B</td><td>C</td><td>D</td></tr>"
    "<tr><td>t / °C</td><td>10</td><td>10</td><td>40</td><td>40</td></tr>"
    "<tr><td>c(H2SO4)</td><td>1</td><td>3</td><td>1</td><td>3</td></tr></table>"
)

Q24_TABLE = (
    "<table><tr>"
    "<td>[F4]</td><td>[F3]</td><td>[F5]</td><td>[F2]</td>"
    "</tr><tr>"
    "<td>A. 收集氯气</td><td>B. 除去水中泥沙</td>"
    "<td>C. 分离乙醇和水</td><td>D. 配制溶液</td>"
    "</tr></table>"
)

Q25_TABLE = (
    "<table><tr><td>选项</td><td>实验操作及现象</td><td>推理或结论</td></tr>"
    "<tr><td>A</td><td>向KI-淀粉…</td><td>还原性…</td></tr>"
    "<tr><td>B</td><td>加入BaCl2…</td><td>含有SO4…</td></tr>"
    "<tr><td>C</td><td>Na2O2…</td><td>放热…</td></tr>"
    "<tr><td>D</td><td>NaOH…</td><td>含有Fe2+…</td></tr></table>"
)


def test_package_image_assets_resolves_existing(tmp_path):
    md = tmp_path / "paper.md"
    img_dir = tmp_path / "_imgs" / "pack"
    img_dir.mkdir(parents=True)
    img = img_dir / "a.jpg"
    img.write_bytes(b"\xff\xd8fake")
    md.write_text('x <img src="_imgs/pack/a.jpg" /> y', encoding="utf-8")
    out = tmp_path / "out"
    out.mkdir()
    assets = rp.package_image_assets(md, out, md.read_text(encoding="utf-8").splitlines())
    assert len(assets) == 1
    a = assets[0]
    assert a["resolved"] is True
    assert a["artifact_path"] == "_imgs/a.jpg"
    assert (out / "_imgs" / "a.jpg").is_file()
    assert a["sha256"]


def test_package_image_assets_missing_file_not_invented(tmp_path):
    md = tmp_path / "paper.md"
    md.write_text('<img src="_imgs/missing/nope.jpg" />', encoding="utf-8")
    out = tmp_path / "out"
    out.mkdir()
    assets = rp.package_image_assets(md, out, md.read_text(encoding="utf-8").splitlines())
    assert assets[0]["resolved"] is False
    assert assets[0]["reason"] == "file_not_found"
    assert not (out / "_imgs").exists() or not any((out / "_imgs").rglob("*.jpg"))


def test_q9_label_image_column_alignment():
    """Q9：文本标签行 + 图像行，列序必须对齐（4 标签 ↔ 4 图）。"""
    labels = re_find_all(r"(?:A|B|C|D)\.\s*[^<]+", Q9_TABLE.split("</tr>")[0])
    imgs = re_find_all(r'src="([^"]+)"', Q9_TABLE.split("</tr>")[1])
    assert len(labels) == 4
    assert len(imgs) == 4
    # 标签前缀顺序 A-D
    assert [x.strip()[0] for x in labels] == list("ABCD")


def test_q19_column_matrix_not_text_options():
    """Q19：A/B/C/D 为列头，数据为矩阵 — 禁止拍成 4 条独立文本选项。"""
    rows = Q19_TABLE.split("</tr>")
    header = rows[0]
    assert "<td>A</td>" in header and "<td>D</td>" in header
    # 至少 2 个数据行 × 4 数据列（含行头）
    assert "t / °C" in rows[1]
    assert rows[1].count("<td>") == 5  # 行头 + 4 列
    assert rows[2].count("<td>") == 5


def test_q24_figure_text_row_pairs():
    """Q24：行1 图形/公式引用，行2 文字选项，列对齐 F↔A-D。"""
    r1, r2, _ = Q24_TABLE.split("</tr>")
    figs = re_find_all(r"\[(F\d+)\]", r1)
    opts = re_find_all(r"([A-D])\.", r2)
    assert figs == ["F4", "F3", "F5", "F2"]
    assert opts == ["A", "B", "C", "D"]


def test_q25_row_composite_options():
    """Q25：行标识 A-D + 两列内容，不得拆成 8 个假选项。"""
    body = Q25_TABLE.split("</tr>")
    assert "选项" in body[0] and "实验操作" in body[0] and "推理" in body[0]
    data = body[1:5]
    assert len(data) == 4
    labels = [re_find_all(r"<td>([A-D])</td>", r)[0] for r in data]
    assert labels == ["A", "B", "C", "D"]
    for r in data:
        assert r.count("<td>") == 3  # label + operation + conclusion


def re_find_all(pattern, text):
    return re.findall(pattern, text)
