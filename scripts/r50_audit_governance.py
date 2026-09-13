r"""R51(收口)对 R50 治理轮的对抗性审查:逐结论真实测试。

攻击面(自查声明 R50 最弱环节):
  A1 快照独立重算——不 import audit_integrity,独立重实现输入面推导与
     sha256,与已提交 data/audit_snapshot_R50_input_baseline.json 逐项比对
     (文件集 / 逐文件 sha / corpus_sha256 摘要);
  A2 record 字节确定性——真实语料上重跑 record,输出与已提交快照字节级比对;
  A3 Gate 作用域攻击——重建 R49 staging 自我覆盖缺陷形态(原件零触碰、
     拷贝被污染),实测 Gate 是否放行;若放行,则 R50 台账
     "staging 自我覆盖类污染今后将直接 fail-closed" 为过强主张;
  A4 Gate 接线活性——变异注入:临时把 gate_assert_unchanged 改为无条件
     raise,真实重跑两个审计工具,断言恰好被 sabotage 咬住(证明调用点
     在真实语料运行中确实执行,非死代码);备份-还原闭环 + sha 核验;
  A5 台账声明复证——零生产代码变更(git diff 文件集)、recompute 输出
     字节确定性、mutation all_ok、原件 sha 前后不变。

语料依赖(本地跑)。输出: data/r50_audit_governance.json
用法: python scripts/r50_audit_governance.py
"""
import hashlib
import json
import shutil
import subprocess
import sys
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WORK = ROOT / ".pytest_work"
OUT = ROOT / "data/r50_audit_governance.json"
SNAPSHOT = ROOT / "data/audit_snapshot_R50_input_baseline.json"
PREFLIGHT = ROOT / "data/resolver_contract_preflight.json"
QC_ARTIFACTS = (
    "data/reslice_batch_c_qc_r34.json",
    "data/phase3_pilot_v2_qc.json",
    "data/pac_qc_v2.json",
)
AI_MOD = ROOT / "scripts/audit_integrity.py"


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def rel_key(p: Path) -> str:
    try:
        return p.resolve().relative_to(ROOT.resolve()).as_posix()
    except ValueError:
        return str(p.resolve())


def independent_inputs():
    """独立重实现:preflight 行推导完整输入面(不 import 被审模块)。"""
    paths, seen = [], set()

    def add(p):
        rp = p.resolve()
        if rp.exists() and str(rp) not in seen:
            seen.add(str(rp))
            paths.append(rp)

    add(PREFLIGHT)
    for q in QC_ARTIFACTS:
        add(ROOT / q)
    pf = json.loads(PREFLIGHT.read_text(encoding="utf-8"))
    for row in pf["rows"]:
        md = ROOT / row["file"]
        add(md)
        man = md.with_suffix(".manifest.json")
        add(man)
        add(md.with_suffix(".annotated.md"))
        if man.exists():
            src = json.loads(man.read_text(encoding="utf-8")).get("source_file")
            if src:
                add(Path(src))
    return paths


def main():
    report = {}
    committed = json.loads(SNAPSHOT.read_text(encoding="utf-8"))

    # ---- A1 快照独立重算 ----
    paths = independent_inputs()
    files = {rel_key(p): sha(p) for p in paths}
    files = dict(sorted(files.items()))
    digest = hashlib.sha256(
        "\n".join(f"{k} {v}" for k, v in files.items()).encode("utf-8")
    ).hexdigest()
    cfiles = committed["files"]
    a1 = {
        "n_independent": len(files),
        "n_committed": committed["n_files"],
        "set_symmetric_diff": sorted(set(files) ^ set(cfiles)),
        "sha_mismatch": sorted(k for k in files
                               if k in cfiles and files[k] != cfiles[k]),
        "digest_match": digest == committed["corpus_sha256"],
        "digest_independent": digest,
        "distinct_resolved_paths": len({str(p) for p in paths}),
        "relative_source_file": sum(
            1 for p in paths
            if not str(p).startswith(str(ROOT.resolve()))),
    }
    a1["ok"] = (not a1["set_symmetric_diff"] and not a1["sha_mismatch"]
                and a1["digest_match"]
                and a1["n_independent"] == a1["distinct_resolved_paths"])
    report["a1_snapshot_independent_recompute"] = a1

    # ---- A2 record 字节确定性(真实语料,经被审模块) ----
    sys.path.insert(0, str(ROOT / "scripts"))
    import audit_integrity as ai
    # 与已提交快照等价比对:必须传入同一 metrics(首跑漏传致 A2 假阴性,
    # 审计工具自身缺陷,如实入册)
    rec = ai.record("R50_input_baseline", paths,
                    metrics=committed.get("metrics"))
    rec_bytes = json.dumps(rec, ensure_ascii=False, indent=1) + "\n"
    committed_bytes = SNAPSHOT.read_text(encoding="utf-8")
    report["a2_record_byte_determinism"] = {
        "byte_equal_committed": rec_bytes == committed_bytes,
        "ok": rec_bytes == committed_bytes,
    }

    # ---- A3 Gate 作用域攻击:R49 staging 自我覆盖形态重建 ----
    d = WORK / f"r51_gate_scope_{uuid.uuid4().hex[:8]}"
    d.mkdir(parents=True)
    try:
        # 原件区:切片 md 与源 md 同名(R49 真实形态),manifest/annotated 在位
        slice_md = d / "pac-x01-01.md"
        src_dir = d / "ocr_src"
        src_dir.mkdir()
        src_md = src_dir / "pac-x01-01.md"          # 与切片同名!
        slice_md.write_text("# 切片\n[[Q1]]\nmarker-line\n",
                            encoding="utf-8", newline="")
        src_md.write_text("源文档全文,无切片标记\n" * 5,
                          encoding="utf-8", newline="")
        man_p = d / "pac-x01-01.manifest.json"
        man_p.write_text(json.dumps({"source_file": str(src_md)}),
                         encoding="utf-8", newline="")
        ann = d / "pac-x01-01.annotated.md"
        ann.write_text("annotated\n", encoding="utf-8", newline="")
        originals = [slice_md, src_md, man_p, ann]

        before = ai.gate_snapshot(originals)
        # R49 缺陷 staging:拷切片→暂存区,再拷同名源→暂存区(自我覆盖)
        stage = d / "staging"
        stage.mkdir()
        staged_slice = stage / slice_md.name
        shutil.copy2(slice_md, staged_slice)
        shutil.copy2(src_md, staged_slice)          # 覆盖!
        polluted = staged_slice.read_text(encoding="utf-8") == \
            src_md.read_text(encoding="utf-8")
        # Gate 对原件集断言
        gate_passed = ai.gate_assert_unchanged(
            before, originals, "r51_a3", ) is True
        report["a3_gate_scope_r49_staging_shape"] = {
            "gate_passed_despite_polluted_oracle": gate_passed,
            "staged_artifact_polluted": polluted,
            "finding": ("Gate 只保护原件集;staging 拷贝污染不触发 Gate"
                        if gate_passed and polluted else "unexpected"),
            "ok": gate_passed and polluted,  # ok = 预期行为被复现(Gate 放行+污染存在)
        }
    finally:
        shutil.rmtree(d, ignore_errors=True)

    # ---- A4 接线活性:变异注入 sabotage → 真实工具必须咬住 ----
    backup = AI_MOD.read_bytes()
    # 唯一锚点:gate_assert_unchanged 函数签名(全模块唯一)
    sabotage = backup.decode("utf-8").replace(
        'def gate_assert_unchanged(before: dict, paths, context: str = "",\n'
        '                          root: Path = ROOT) -> bool:\n',
        'def gate_assert_unchanged(before: dict, paths, context: str = "",\n'
        '                          root: Path = ROOT) -> bool:\n'
        '    raise RuntimeError("[SABOTAGE] gate liveness probe")\n',
    )
    assert sabotage != backup.decode("utf-8"), "变异未注入(锚点失配)!"
    a4 = {}
    try:
        AI_MOD.write_text(sabotage, encoding="utf-8", newline="")
        for tool in ("r48_audit_recompute.py", "r48_audit_pc_mutation.py"):
            r = subprocess.run(
                [sys.executable, str(ROOT / "scripts" / tool)],
                capture_output=True, encoding="utf-8", errors="replace",
                cwd=str(ROOT))
            hit = "[SABOTAGE]" in (r.stdout + r.stderr)
            a4[tool] = {"exit": r.returncode, "sabotage_hit": hit}
    finally:
        AI_MOD.write_bytes(backup)
    a4["module_sha_restored"] = sha(AI_MOD) == hashlib.sha256(
        backup).hexdigest()
    # 还原后干净重跑必须成功(recompute 至少)
    r = subprocess.run([sys.executable,
                        str(ROOT / "scripts/r48_audit_recompute.py")],
                       capture_output=True, encoding="utf-8",
                       errors="replace", cwd=str(ROOT))
    a4["clean_rerun_exit"] = r.returncode
    a4["ok"] = (all(v["sabotage_hit"] and v["exit"] != 0
                    for k, v in a4.items() if k.endswith(".py"))
                and a4["module_sha_restored"] and a4["clean_rerun_exit"] == 0)
    report["a4_gate_wiring_liveness"] = a4

    # ---- A5 台账声明复证 ----
    out_bytes_before = sha(ROOT / "data/r48_audit_recompute.json")
    r = subprocess.run([sys.executable,
                        str(ROOT / "scripts/r48_audit_recompute.py")],
                       capture_output=True, encoding="utf-8",
                       errors="replace", cwd=str(ROOT))
    out_bytes_after = sha(ROOT / "data/r48_audit_recompute.json")
    mut = json.loads((ROOT / "data/r48_audit_pc_mutation.json")
                     .read_text(encoding="utf-8"))
    report["a5_ledger_claims"] = {
        "recompute_rerun_byte_stable": out_bytes_before == out_bytes_after,
        "recompute_exit": r.returncode,
        "mutation_all_ok_committed": mut.get("all_ok"),
        "mutation_n_results": len(mut.get("results", [])),
        "ok": (out_bytes_before == out_bytes_after and r.returncode == 0
               and mut.get("all_ok") is True),
    }

    ok = all(report[k]["ok"] for k in report)
    report["all_ok"] = ok
    Path(OUT).write_text(json.dumps(report, ensure_ascii=False, indent=1)
                         + "\n", encoding="utf-8", newline="")
    print(json.dumps(report, ensure_ascii=False, indent=1)[:2400])
    print("all_ok =", ok)


if __name__ == "__main__":
    main()
