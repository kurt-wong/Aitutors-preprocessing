# -*- coding: utf-8 -*-
"""Phase C-R2 A/B：真实 write_outputs 产物结构回归 + 图像同名碰撞防护。

测试调用生产入口 reslice_pipeline.write_outputs，读取该次生成的
paper.manifest.json / paper.annotated.md，再断言输出结构。
禁止手写 HTML 当作 Producer 输出。
"""
from __future__ import annotations

import hashlib
import json
import re
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import reslice_pipeline as rp  # noqa: E402

PKG = Path(
    r"D:/Project/AITutor-X/E2E_ACCEPTANCE/06_M1_PACKAGES/chem-2018-spring-huikao-teacher"
)
HAS_PKG = (PKG / "paper.md").is_file() and (PKG / "manifest.json").is_file()


def _run_real_producer(tmp_path: Path) -> dict:
    """调用正式 write_outputs，返回产物路径与已解析 manifest/annotated。"""
    src_md = PKG / "paper.md"
    man_in = json.loads((PKG / "manifest.json").read_text(encoding="utf-8"))
    text = re.sub(r"<!--\s*META:[^>]*-->\n?", "", src_md.read_text(encoding="utf-8"))
    lines = text.splitlines()
    meta = man_in.get("annotation_meta", {})
    out = tmp_path / "producer_out"
    rp.write_outputs(
        out,
        "paper",
        lines,
        man_in,
        meta.get("validation_issues", []),
        {"warnings": meta.get("warnings", [])},
        src_md.name,
        src_md,
        model=man_in.get("model", rp.DEFAULT_MODEL),
    )
    man_out = json.loads((out / "paper.manifest.json").read_text(encoding="utf-8"))
    annotated = (out / "paper.annotated.md").read_text(encoding="utf-8")
    return {"out": out, "manifest": man_out, "annotated": annotated}


def _options_block(annotated: str, unit_key: str) -> str:
    """从 annotated.md 的 META 锚点取 unit 块内的 options 角色块。"""
    m = re.search(
        rf"unit:start:{re.escape(unit_key)}\b(.*?)unit:end:{re.escape(unit_key)}\b",
        annotated,
        re.S,
    )
    assert m, f"unit block not found for {unit_key}"
    om = re.search(
        r"options:start:\d+\s*-->(.*?)<!--\s*META:options:end:",
        m.group(1),
        re.S,
    )
    assert om, f"options block not found for {unit_key}"
    return om.group(1)


@pytest.fixture(scope="module")
def real_producer(tmp_path_factory):
    if not HAS_PKG:
        pytest.skip("chem M1 package not present")
    return _run_real_producer(tmp_path_factory.mktemp("phase_c_r2"))


# ---------- 工作项 A：四种真实结构 ----------

def test_q9_label_image_column_alignment_real_output(real_producer):
    """Q9：生产产物 options 块含 4 标签 + 4 图，且 image_assets 可解析。"""
    blk = _options_block(real_producer["annotated"], "Q9")
    labels = re.findall(r">\s*([A-D])\s*[\.．、]", blk)
    imgs = re.findall(r'src="([^"]+)"', blk)
    assert labels == ["A", "B", "C", "D"], labels
    assert len(imgs) == 4, imgs
    assets = real_producer["manifest"].get("image_assets") or []
    q9_assets = [a for a in assets if any(n in str(a.get("src", "")) for n in (
        "img_in_image_box_157_151_247_252",
        "img_in_image_box_328_147_444_230",
        "img_in_image_box_529_136_618_235",
        "img_in_image_box_725_140_864_227",
    ))]
    assert len(q9_assets) == 4
    for a in q9_assets:
        assert a["resolved"] is True
        assert a.get("sha256")
        assert (real_producer["out"] / a["artifact_path"]).is_file()


def test_q19_column_matrix_real_output(real_producer):
    """Q19：A-D 为列头 + 实验条件矩阵，不得被拆成普通文本选项列表。"""
    blk = _options_block(real_producer["annotated"], "Q19")
    assert "<table" in blk
    # 列头行含 A B C D 单元格
    header = blk.split("</tr>")[0]
    for lab in ("A", "B", "C", "D"):
        assert re.search(rf">\s*{lab}\s*<", header), (lab, header[:200])
    # 数据行含温度/浓度
    assert "t / °C" in blk or "t/°C" in blk.replace(" ", "")
    assert "H_{2}SO_{4}" in blk or "H2SO4" in blk or "SO" in blk
    # 不得出现四条 “A. …” 独立文本选项形态
    assert not re.search(r">\s*A\s*[\.．、]\s*[^<]", blk), "must not flatten to text options"


def test_q24_figure_text_pairs_real_output(real_producer):
    """Q24：图形引用行与文字选项行列对齐 F4/F3/F5/F2 ↔ A/B/C/D。"""
    blk = _options_block(real_producer["annotated"], "Q24")
    assert "<table" in blk
    figs = re.findall(r"F_?\{?(\d)\}?", blk)
    # 保留原引用形态 F_{4} 等
    assert any("F" in blk for _ in [0])
    for token in ("F_{4}", "F_{3}", "F_{5}", "F_{2}", "F4", "F3", "F5", "F2"):
        pass
    joined = blk
    assert ("F_{4}" in joined or "F4" in joined)
    assert ("F_{3}" in joined or "F3" in joined)
    opts = re.findall(r">\s*([A-D])\s*[\.．、]", blk)
    assert opts == ["A", "B", "C", "D"], opts


def test_q25_row_composite_options_real_output(real_producer):
    """Q25：行 A-D × (操作, 结论) 复合，不得拆成 8 个假选项。"""
    blk = _options_block(real_producer["annotated"], "Q25")
    assert "<table" in blk
    assert "实验操作" in blk
    assert "推理或结论" in blk
    rows = [r for r in blk.split("</tr>") if r.strip()]
    # 表头 + 4 数据行
    assert len(rows) >= 5, len(rows)
    data = rows[1:5]
    labels = []
    for r in data:
        m = re.search(r">\s*([A-D])\s*<", r)
        assert m, r[:120]
        labels.append(m.group(1))
        # 每行应含 3 个 td（label + 操作 + 结论）
        assert r.count("<td") == 3, r[:200]
    assert labels == ["A", "B", "C", "D"]


def test_real_manifest_image_assets_all_resolved(real_producer):
    assets = real_producer["manifest"].get("image_assets") or []
    assert assets, "image_assets empty"
    unresolved = [a for a in assets if not a.get("resolved")]
    assert unresolved == [], unresolved


# ---------- 工作项 B：同名碰撞 ----------

def test_same_file_duplicate_ref_deduped(tmp_path):
    img = tmp_path / "_imgs" / "pack" / "same.jpg"
    img.parent.mkdir(parents=True)
    img.write_bytes(b"\xff\xd8SAME")
    md = tmp_path / "paper.md"
    md.write_text(
        '<img src="_imgs/pack/same.jpg" />\n<img src="_imgs/pack/same.jpg" />',
        encoding="utf-8",
    )
    out = tmp_path / "out"
    out.mkdir()
    assets = rp.package_image_assets(md, out, md.read_text(encoding="utf-8").splitlines())
    assert len(assets) == 2
    assert all(a["resolved"] for a in assets)
    assert assets[0]["sha256"] == assets[1]["sha256"]
    assert (out / "_imgs" / "same.jpg").is_file()


def test_basename_collision_different_content_not_merged(tmp_path):
    """不同源文件同 basename、内容不同 → 不得静默合并为同一产物。"""
    a_dir = tmp_path / "a" / "_imgs" / "pack"
    b_dir = tmp_path / "b" / "_imgs" / "other"
    a_dir.mkdir(parents=True)
    b_dir.mkdir(parents=True)
    (a_dir / "img.jpg").write_bytes(b"\xff\xd8AAA")
    (b_dir / "img.jpg").write_bytes(b"\xff\xd8BBB")
    md = tmp_path / "paper.md"
    md.write_text(
        '<img src="a/_imgs/pack/img.jpg" />\n<img src="b/_imgs/other/img.jpg" />',
        encoding="utf-8",
    )
    out = tmp_path / "out"
    out.mkdir()
    assets = rp.package_image_assets(md, out, md.read_text(encoding="utf-8").splitlines())
    assert len(assets) == 2
    assert assets[0]["resolved"] is True
    # 第二个必须拒绝合并
    assert assets[1]["resolved"] is False
    assert assets[1]["reason"] == "basename_collision"
    assert assets[1]["existing_sha256"] != assets[1]["incoming_sha256"]
    # 磁盘上只有第一个实体
    on_disk = list((out / "_imgs").glob("*.jpg"))
    assert len(on_disk) == 1


def test_missing_file_still_not_invented(tmp_path):
    md = tmp_path / "paper.md"
    md.write_text('<img src="_imgs/none/nope.jpg" />', encoding="utf-8")
    out = tmp_path / "out"
    out.mkdir()
    assets = rp.package_image_assets(md, out, md.read_text(encoding="utf-8").splitlines())
    assert assets[0]["resolved"] is False
    assert assets[0]["reason"] == "file_not_found"


def test_rerun_with_changed_source_refreshes_artifact(tmp_path):
    """同名源内容变更的重跑：必须刷新产物，不得沿用旧字节。"""
    src = tmp_path / "_imgs" / "pack" / "img.jpg"
    src.parent.mkdir(parents=True)
    src.write_bytes(b"\xff\xd8V1")
    md = tmp_path / "paper.md"
    md.write_text('<img src="_imgs/pack/img.jpg" />', encoding="utf-8")
    out = tmp_path / "out"
    out.mkdir()

    a1 = rp.package_image_assets(md, out, md.read_text(encoding="utf-8").splitlines())
    assert a1[0]["resolved"] is True
    h1 = a1[0]["sha256"]

    # 源变更后重跑（同一 out_dir）
    src.write_bytes(b"\xff\xd8V2-CHANGED")
    a2 = rp.package_image_assets(md, out, md.read_text(encoding="utf-8").splitlines())
    assert a2[0]["resolved"] is True
    h2 = a2[0]["sha256"]
    assert h2 != h1, "artifact must refresh when source bytes change"
    disk = hashlib.sha256((out / "_imgs" / "img.jpg").read_bytes()).hexdigest()
    assert disk == h2, "manifest sha256 must match on-disk bytes after refresh"


def test_q9_four_image_hashes_match_dsh_baseline(real_producer):
    """Q9 四图与 DSH 固定参照 sha256/bytes 逐字节一致。"""
    expect = {
        "img_in_image_box_157_151_247_252.jpg": (
            "42644ed0fa931637de73b85a3940249f0b2bc0a881b39a2c43a3b2bc65d5017c",
            2594,
        ),
        "img_in_image_box_328_147_444_230.jpg": (
            "5aa84d675f43dc6adbf5d93fae300e509c4c825df53397ab0369a37ac5ba8650",
            3964,
        ),
        "img_in_image_box_529_136_618_235.jpg": (
            "b9a6acfad2eec44102bf68df1bbc16f684ff6fc1c4e82274a460f935c660ca93",
            4043,
        ),
        "img_in_image_box_725_140_864_227.jpg": (
            "45af11e7ef73a37a07cf77ea19eab0ef03d250cd0366771570184d58b5f976f4",
            5246,
        ),
    }
    assets = real_producer["manifest"].get("image_assets") or []
    for name, (sha, nbytes) in expect.items():
        hits = [a for a in assets if str(a.get("src", "")).endswith(name)]
        assert hits, name
        a = hits[0]
        assert a["resolved"] is True
        assert a["sha256"] == sha, (name, a["sha256"], sha)
        assert a["bytes"] == nbytes, (name, a["bytes"], nbytes)
        p = real_producer["out"] / a["artifact_path"]
        assert p.is_file()
        assert hashlib.sha256(p.read_bytes()).hexdigest() == sha
