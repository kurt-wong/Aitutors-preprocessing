r"""审计治理机制(R50 落地,R49 用户建议转实施;R51 对抗审查收口):

1) **Input Integrity Gate**:审计工具执行前后,**原件输入文件集**的 sha256
   必须逐个不变(before == after),不一致即 RuntimeError 失败。
   动机出处:R46 BUG-29 家族(审查/变异代码吞真实工件)与 Test Oracle
   Pollution 总类。**作用域限定(R51 A3 实测)**:不覆盖 staging 拷贝污染
   (R49 自我覆盖家族)——拷贝保真由控制组检查负责,两道防线缺一不可。

2) **Audit Snapshot Manifest**:审计输入集(+度量)的确定性快照;后续报告
   引用快照摘要(如 `R50_input_baseline@sha256:xxxx`)而非引用动态目录,
   消除 Audit Snapshot Drift(BUG-30 类:R19 时点"14 份/304 单元"在
   R31/R37 fix 链再生成 manifest 后变为 15/305,历史数字不可逐位复现)。

纪律:record 输出确定性——同一输入集生成字节级相同的快照(不含时间戳),
可直接入库、可 sha 对账。

用法:
  python scripts/audit_integrity.py record <audit_id> \
      [--preflight data/resolver_contract_preflight.json] \
      [--extra data/xxx.json ...] [--metrics-json '{"k": v}']
  python scripts/audit_integrity.py verify <audit_id 或快照文件路径>

快照落点: data/audit_snapshot_<audit_id>.json
"""
import argparse
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SNAPSHOT_PREFIX = "data/audit_snapshot_"

# R48/R49 结论的完整输入面:preflight 之外的三份已提交 QC 工件
QC_ARTIFACTS = (
    "data/reslice_batch_c_qc_r34.json",
    "data/phase3_pilot_v2_qc.json",
    "data/pac_qc_v2.json",
)


def sha256_file(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def rel_key(p: Path, root: Path = ROOT) -> str:
    """快照键:root 之下取相对 posix 路径,root 之外保留绝对路径。"""
    p = Path(p)
    try:
        return p.resolve().relative_to(Path(root).resolve()).as_posix()
    except ValueError:
        return str(p.resolve())


def snapshot(paths, root: Path = ROOT):
    """输入集 -> {rel_key: sha256},按键排序(确定性)。"""
    files = {}
    for p in paths:
        p = Path(p)
        if not p.exists():
            raise FileNotFoundError(f"audit input missing: {p}")
        files[rel_key(p, root)] = sha256_file(p)
    return dict(sorted(files.items()))


def gate_snapshot(paths, root: Path = ROOT):
    """Input Integrity Gate:执行前快照。"""
    return snapshot(paths, root)


def gate_assert_unchanged(before: dict, paths, context: str = "",
                          root: Path = ROOT) -> bool:
    """Input Integrity Gate:执行后断言输入集零漂移,不一致即抛。

    作用域(R51 A3 实测限定):只保证**原件集**在审查运行前后不变,
    防御 R46 BUG-29 家族(变异/审查代码吞真实工件);**不覆盖** staging
    拷贝污染(R49 自我覆盖家族)——拷贝保真仍由控制组检查负责。
    新增输入文件由调用方加入 paths 列表声明(gate_snapshot 即校验存在;
    R51 删除了不可达的 added 分支:前后同一 paths 派生键集,added 恒空)。
    """
    after = {}
    missing = []
    for p in paths:
        p = Path(p)
        if not p.exists():
            missing.append(rel_key(p, root))
            continue
        after[rel_key(p, root)] = sha256_file(p)
    drift = sorted(k for k, v in before.items() if after.get(k) != v)
    if drift or missing:
        raise RuntimeError(
            f"[audit-integrity] input drift in {context or 'audit'}: "
            f"changed={drift} missing={missing}")
    return True


def inputs_from_preflight(preflight_path, root: Path = ROOT):
    """从 preflight 工件推导完整输入面:
    preflight json 本身 + 每行的切片 md / manifest / annotated 兄弟件 / 源文件。"""
    preflight_path = Path(preflight_path)
    root = Path(root)
    pf = json.loads(preflight_path.read_text(encoding="utf-8"))
    paths, seen = [], set()

    def add(p):
        p = Path(p)
        if p.exists() and str(p) not in seen:
            seen.add(str(p))
            paths.append(p)

    add(preflight_path)
    for row in pf.get("rows", []):
        md = root / row["file"]
        add(md)
        man = md.with_suffix(".manifest.json")
        add(man)
        add(md.with_suffix(".annotated.md"))
        if man.exists():
            src = json.loads(man.read_text(encoding="utf-8")).get("source_file")
            if src:
                add(Path(src))
    return paths


def record(audit_id: str, paths, metrics=None, root: Path = ROOT) -> dict:
    """Audit Snapshot Manifest:确定性快照(无时间戳,字节可复现)。"""
    files = snapshot(paths, root)
    digest = hashlib.sha256(
        "\n".join(f"{k} {v}" for k, v in files.items()).encode("utf-8")
    ).hexdigest()
    return {
        "audit_id": audit_id,
        "n_files": len(files),
        "corpus_sha256": digest,
        "metrics": metrics or {},
        "files": files,
    }


def snapshot_path(audit_id: str, root: Path = ROOT) -> Path:
    return Path(root) / f"{SNAPSHOT_PREFIX}{audit_id}.json"


def write_record(rec: dict, root: Path = ROOT) -> Path:
    out = snapshot_path(rec["audit_id"], root)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(rec, ensure_ascii=False, indent=1) + "\n",
                   encoding="utf-8", newline="")
    return out


def load_record(id_or_path, root: Path = ROOT) -> dict:
    p = Path(id_or_path)
    if not p.exists():
        p = snapshot_path(str(id_or_path), root)
    return json.loads(p.read_text(encoding="utf-8"))


def verify(rec: dict, root: Path = ROOT) -> dict:
    """重算快照内每个文件的当前 sha256,报告漂移/缺失。"""
    root = Path(root)
    drift, missing = [], []
    for key, old_sha in rec["files"].items():
        p = Path(key) if Path(key).is_absolute() else root / key
        if not p.exists():
            missing.append(key)
        elif sha256_file(p) != old_sha:
            drift.append(key)
    return {"ok": not drift and not missing,
            "drift": sorted(drift), "missing": sorted(missing),
            "n_files": rec["n_files"]}


def main(argv=None):
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("record")
    r.add_argument("audit_id")
    r.add_argument("--preflight")
    r.add_argument("--extra", nargs="*", default=[])
    r.add_argument("--metrics-json", default="{}")
    v = sub.add_parser("verify")
    v.add_argument("audit_id")
    a = ap.parse_args(argv)

    if a.cmd == "record":
        paths = []
        if a.preflight:
            paths += inputs_from_preflight(ROOT / a.preflight)
        for e in a.extra:
            paths.append(ROOT / e)
        for q in QC_ARTIFACTS:  # preflight 场景默认纳入三份 QC 工件
            qp = ROOT / q
            if a.preflight and qp.exists() and qp not in paths:
                paths.append(qp)
        rec = record(a.audit_id, paths, metrics=json.loads(a.metrics_json))
        out = write_record(rec)
        print(f"wrote {out} n_files={rec['n_files']} "
              f"corpus_sha256={rec['corpus_sha256'][:16]}")
    else:
        rec = load_record(a.audit_id)
        res = verify(rec)
        print(json.dumps(res, ensure_ascii=False))
        if not res["ok"]:
            sys.exit(1)


if __name__ == "__main__":
    main()
