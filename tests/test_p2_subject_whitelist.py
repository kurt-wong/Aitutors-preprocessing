"""P2 — Producer subject/grade 白名单 + preserve 修复的针对性测试。"""
import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from reslice_pipeline import (  # noqa: E402
    VALID_SUBJECTS,
    grade_subject_from_rel_path,
)


class TestSubjectWhitelist:
    """已知学科从规范化相对路径正确推导。"""

    @pytest.mark.parametrize("rel,expected", [
        ("会考/物理/x.md", "物理"),
        ("会考/化学/x.md", "化学"),
        ("会考/生物/x.md", "生物"),
        ("会考/地理/x.md", "地理"),
        ("会考/数学/x.md", "数学"),
        ("会考/语文/x.md", "语文"),
        ("会考/英语/x.md", "英语"),
        ("高一/物理/x.md", "物理"),
        ("高二/化学/x.md", "化学"),
        ("高三/数学/x.md", "数学"),
        ("高考真题/英语/x.md", "英语"),
        ("合格考/历史/x.md", "历史"),
        ("竞赛自招/政治/x.md", "政治"),
    ])
    def test_known_subjects(self, rel, expected):
        _, subject, _ = grade_subject_from_rel_path(rel)
        assert subject == expected

    @pytest.mark.parametrize("rel", [
        "会考/x.md",                    # 只有一段，无学科段
        "gen-test-runs/run-20261013-PHY-001/x.md",  # run 名不是学科
        "reslice-pac/ocr/x.md",         # ocr 不是学科
        "phase-c-r2-producer-out/paper.md",  # paper.md 无学科依据
        "Project/something/x.md",       # Project 不是学科
        "",                             # 空路径
        "x.md",                         # 单段文件名
    ])
    def test_non_subject_paths_yield_none(self, rel):
        _, subject, _ = grade_subject_from_rel_path(rel)
        assert subject is None, f"{rel!r} must not produce subject, got {subject!r}"

    def test_lizong_not_subject(self):
        """理综是综合科目，不是单一学科。"""
        _, subject, _ = grade_subject_from_rel_path("其他汇编/理综/x.md")
        assert subject is None

    def test_wenzong_not_subject(self):
        _, subject, _ = grade_subject_from_rel_path("高考真题/文综/x.md")
        assert subject is None

    def test_huikao_keyword_not_subject(self):
        """会考/合格考是考试类型层级，不得误判为学科。"""
        _, subject, _ = grade_subject_from_rel_path("会考/合格考/x.md")
        assert subject is None

    def test_valid_subjects_set(self):
        """白名单复用语料目录层级的既有学科值域。"""
        assert VALID_SUBJECTS == frozenset({
            "化学", "历史", "地理", "政治", "数学", "物理", "生物", "英语", "语文",
        })


class TestGradeSafety:
    """grade 同样不得因兜底写出错误值。"""

    def test_known_grade_keywords(self):
        g, _, src = grade_subject_from_rel_path("高一/物理/x.md")
        assert g == "高一" and src == "path_keyword:高一"

    def test_huikao_maps_to_gaoyi(self):
        g, _, src = grade_subject_from_rel_path("会考/物理/x.md")
        assert g == "高一" and "会考" in src

    def test_fallback_grade_is_none(self):
        """无法判定时 grade 保留 None，不得兜底写高三。"""
        g, _, src = grade_subject_from_rel_path("reslice-pac/ocr/x.md")
        assert g is None, f"fallback must not write grade, got {g!r}"
        assert src == "fallback"


class TestPreserveLogic:
    """write_outputs preserve：非 None 保留，None/缺失 → 推导。"""

    def _make_src(self, tmp_path, rel_under_src="会考/物理/test.md"):
        """构造 SRC_ROOT 下的源文件并返回 (src_path, SRC_ROOT)。"""
        src_root = tmp_path / "Ocr-markdown"
        src = src_root / rel_under_src
        src.parent.mkdir(parents=True, exist_ok=True)
        src.write_text("line1\nline2\n", encoding="utf-8")
        return src, src_root

    def _run_write_outputs(self, tmp_path, man_extra, rel_under_src="会考/物理/test.md"):
        from reslice_pipeline import write_outputs
        import reslice_pipeline as rp

        src, src_root = self._make_src(tmp_path, rel_under_src)
        old_src_root = rp.SRC_ROOT
        rp.SRC_ROOT = src_root
        try:
            out_dir = tmp_path / "out"
            man = {
                "units": [{"unit_id": "Q1", "unit_type": "standalone_question",
                           "question_numbers": [1], "original_question_type": "short_answer",
                           "stem_lines": [1, 1], "answer_lines": [2, 2]}],
                **man_extra,
            }
            write_outputs(out_dir, "test", ["l1", "l2"], man, [],
                          {"warnings": []}, "test.md", src)
            manifest_path = out_dir / "test.manifest.json"
            return json.loads(manifest_path.read_text(encoding="utf-8"))
        finally:
            rp.SRC_ROOT = old_src_root

    def test_explicit_null_subject_backfilled(self, tmp_path):
        m = self._run_write_outputs(tmp_path, {"subject": None, "grade": "高一"})
        assert m["subject"] == "物理"
        assert m["grade"] == "高一"  # 非 None 保留

    def test_non_null_subject_preserved(self, tmp_path):
        m = self._run_write_outputs(tmp_path, {"subject": "化学", "grade": "高一"})
        assert m["subject"] == "化学"  # 不被路径推导覆盖

    def test_missing_keys_backfilled(self, tmp_path):
        m = self._run_write_outputs(tmp_path, {})
        assert m["subject"] == "物理"
        assert m["grade"] == "高一"

    def test_explicit_null_grade_backfilled(self, tmp_path):
        m = self._run_write_outputs(tmp_path, {"grade": None, "subject": None})
        assert m["grade"] == "高一"
        assert m["subject"] == "物理"

    def test_unreliable_path_keeps_none(self, tmp_path):
        m = self._run_write_outputs(
            tmp_path, {"subject": None, "grade": None},
            rel_under_src="reslice-pac/ocr/test.md",
        )
        assert m["subject"] is None
        assert m["grade"] is None

    def test_paper_md_no_guess(self, tmp_path):
        """paper.md 无可靠学科段 → 不猜测。"""
        m = self._run_write_outputs(
            tmp_path, {"subject": None},
            rel_under_src="phase-c-r2-producer-out/paper.md",
        )
        assert m["subject"] is None

    def test_source_file_format_not_parsed(self, tmp_path):
        """source_file 字符串形态不参与推导 — 只用 rel_out 规范化路径。"""
        m = self._run_write_outputs(
            tmp_path,
            {"subject": None, "source_file": "C:\\Weird\\Path\\物理\\fake.md"},
            rel_under_src="高一/数学/test.md",
        )
        # 推导依据是 rel_out(src_path, SRC_ROOT) = 高一/数学/test.md
        assert m["subject"] == "数学"


class TestRecompileRelativePath:
    """P2-FIX — recompile_outputs 真实调用链：相对 source_file 必须正确解析。

    不直接测 grade_subject_from_rel_path，而是走 recompile_outputs 全链路，
    覆盖 manifest.source_file 为相对路径时的实际形态。
    """

    def _setup_recompile(self, tmp_path, rel_under_root="Ocr-markdown/会考/物理/test.md",
                         source_file_value=None):
        """构造 ROOT/Ocr-markdown/... 源文件 + manifest，返回 (recompile_outputs, out_root, ROOT)。"""
        import reslice_pipeline as rp

        root = tmp_path
        src = root / rel_under_root
        src.parent.mkdir(parents=True, exist_ok=True)
        src.write_text("[L0001] 题干\n[L0002] 答案\n", encoding="utf-8")

        out_root = root / "out" / "会考" / "物理"
        out_root.mkdir(parents=True, exist_ok=True)
        sf = source_file_value or rel_under_root  # relative by default
        manifest = {
            "source_file": sf,
            "model": "test-model",
            "annotation_meta": {"prompt_version": "test-v1",
                                "validation_issues": [], "warnings": []},
            "units": [{
                "unit_id": "Q1", "unit_type": "standalone_question",
                "question_numbers": [1], "original_question_type": "short_answer",
                "stem_lines": [1, 1], "answer_lines": [2, 2],
            }],
            "subject": None,
            "grade": None,
        }
        mf = out_root / "test.manifest.json"
        mf.write_text(json.dumps(manifest, ensure_ascii=False), encoding="utf-8")

        # Monkey-patch ROOT and SRC_ROOT to tmp_path
        old_root, old_src_root = rp.ROOT, rp.SRC_ROOT
        rp.ROOT = root
        rp.SRC_ROOT = root / "Ocr-markdown"
        try:
            n = rp.recompile_outputs(out_root)
        finally:
            rp.ROOT = old_root
            rp.SRC_ROOT = old_src_root
        return json.loads(mf.read_text(encoding="utf-8")), n

    def test_relative_source_file_backfills_subject(self, tmp_path):
        """相对 source_file + 会考/物理 → subject=物理。"""
        m, n = self._setup_recompile(tmp_path)
        assert n == 1
        assert m["subject"] == "物理"
        assert m["grade"] == "高一"

    def test_relative_source_file_chemistry(self, tmp_path):
        m, _ = self._setup_recompile(
            tmp_path,
            rel_under_root="Ocr-markdown/合格考/化学/test.md",
            source_file_value="Ocr-markdown/合格考/化学/test.md",
        )
        assert m["subject"] == "化学"

    def test_absolute_source_file_still_works(self, tmp_path):
        """绝对路径行为不回退。"""
        src_abs = tmp_path / "Ocr-markdown" / "高一" / "数学" / "test.md"
        m, _ = self._setup_recompile(
            tmp_path,
            rel_under_root="Ocr-markdown/高一/数学/test.md",
            source_file_value=str(src_abs),
        )
        assert m["subject"] == "数学"

    def test_relative_variants(self, tmp_path):
        """不同相对形态（./ 前缀、反斜杠）都正确解析。"""
        m, _ = self._setup_recompile(
            tmp_path,
            rel_under_root="Ocr-markdown/会考/生物/test.md",
            source_file_value="Ocr-markdown\\会考\\生物\\test.md",
        )
        assert m["subject"] == "生物"

    def test_missing_source_raises(self, tmp_path):
        """源文件不存在 → 明确失败，不静默生成错误元数据。"""
        import reslice_pipeline as rp

        out_root = tmp_path / "out"
        out_root.mkdir(parents=True)
        mf = out_root / "test.manifest.json"
        mf.write_text(json.dumps({
            "source_file": "Ocr-markdown/会考/物理/nonexistent.md",
            "annotation_meta": {"prompt_version": "t", "validation_issues": [], "warnings": []},
            "units": [],
        }), encoding="utf-8")

        old_root = rp.ROOT
        rp.ROOT = tmp_path
        try:
            with pytest.raises(FileNotFoundError):
                rp.recompile_outputs(out_root)
        finally:
            rp.ROOT = old_root
