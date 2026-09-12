# -*- coding: utf-8 -*-
"""PAC 第一轮逐样本全 stage 轨迹汇总(设计稿 §4 schema 的落地形态)。

合并:selection(源) + pac_track_ocr.json(OCR) + 批注 result(LLM) +
pac_qc_v2.json(QC) + 回填报告(identity) + 工件盘点(artifact);
resolver/compiler/gate/admission 如实记 NOT_BUILT。
human_review 记录复核方式与结论(深度复核=hazard 文件逐项实测;
抽验=QC PASS + 局部人读,如实标注,不冒充逐题全查)。

输出 data/pac_track_round1.json。用法:python scripts/pac_assemble_tracks.py
"""

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "Ocr-markdown/reslice-pac-annotated/reslice-pac/ocr"

# 人工复核记录(2026-09-13,复核人:assistant,依据真实读盘/探针实测)
REVIEW = {
    "pac-c01-01": ("深度", "PASS", "题号覆盖 30/30 无缺号重号;语义探针 0 报警;identity 0 fail"),
    "pac-c01-02": ("深度", "PASS", "覆盖 28/28;探针 P13×7 全为括号答案键格式盲区((21)(22) 连写行);"
                                   "**printed 零回收:源卷题号为 (1)(2)(3) 括号式,回填解析正则只认 NN. 前缀 → 28/28 unverified**"
                                   "(已知回收边界,非缺陷;printed_provenance=unknown 如实未伪造;列入硬化候选)"),
    "pac-c02-01": ("深度", "PASS", "覆盖 26/26;P13×1+P14×4 全为子问编号(1)2)3))盲区;真扫描件链路完整"),
    "pac-c02-02": ("深度", "PASS", "覆盖 32/32;P14×4 为材料内编号(1.-4. 论述要点)盲区"),
    "pac-c05-01": ("深度", "PASS", "已知 hazard 卷:新鲜 OCR esc_dot 2→2 复现且 0 误升分节(BUG-25 修复在新数据上成立);QC 0 issue"),
    "pac-c05-02": ("深度", "PASS", "覆盖 21/21;语义探针 0 报警;identity 0 fail"),
    "pac-c06-01": ("深度", "PASS", "已知丢图/裸LaTeX 卷:新鲜 OCR esc_dot 1→1 复现;QC 0 issue(当年缺陷未复现,如实记录)"),
    "pac-c06-02": ("深度", "PASS", "OCR 漂移实证:历史跑答案行为普通行、本次跑 12 处升为 ### 标题(同位置同内容,随机性);下游 QC 仍 0 issue=对结构漂移鲁棒"),
    "pac-c07-01": ("深度", "FAIL", "BUG-17 家族如实暴露:8 题 C3 答案区空 + C5 11 图未覆盖 + C11 复述相似 0.96;FAIL 非静默"),
    "pac-c07-02": ("深度", "PASS", "覆盖 21/21;P15×1 为答案内子问标记(2))盲区"),
    "pac-c08-01": ("深度", "PASS", "覆盖 44/44(9 单元整块化);P13×1 区间连写格式盲区(35-39 DEFGB);P14/P15×17 全为写作提示/评分细则内部编号盲区(评分细则归 answer 区符合约定)"),
    "pac-c08-02": ("深度", "PASS", "覆盖 20/20;语义探针 0 报警"),
    "pac-c09-01": ("深度", "FAIL", "BUG-22 卷:新鲜 LLM 按 prompt v2.3 输出 printed(1-9)与 canonical(答案键 26-34)分离正确,identity 0 fail;探针 P14×9 全为 printed/canonical 错位盲区(探针系 v2 前所写,反证 v2 生效);6 题 C3 答案区空(源面答案缺失族)→ QC 如实 FAIL"),
    "pac-c09-02": ("深度", "FAIL", "explicit Q96 卷:C9 结构行混入 L422 注意事项 → FAIL 如实;题号 96 覆盖正确(units=35 题=96);P13×1(写作答案'略')源面忠实"),
    "pac-c10-01": ("深度", "PASS", "IMAGE_DANGLING 卷:新鲜产物 C5=0(未覆盖图检查),当年缺陷未复现,如实记录"),
    "pac-c10-02": ("深度", "PASS", "OCR 漂移实证第二例:6 处答案行本次升 ### 标题(历史无);QC 仍 0 issue"),
    "pac-c11-01": ("深度", "PASS", "三十一中化学:L324 注记分节标题在新鲜 OCR 逐字复现(新 L325,全文偏移 1 行),BUG-24 修复后被正确建模为分节(QC 0 issue,identity 0 fail);探针 P14×12/P15×3 为填空题 printed(1-11)/canonical(46-56) 错位盲区;keep 三方裁决仍独立挂起,与本链路结果无关"),
    "pac-c11-02": ("深度", "FAIL", "行融合复现:L137 分节标题+题1+【答案】B 三重融合,被 SectionLocator 如实收为 section start(标题文本污染,ACCEPTED OCR LIMITATION 家族),下游 C7/C9 咬住 → FAIL 非静默"),
    "pac-c12-01": ("深度", "PASS", "BUG-25 台账卷:L266/L274 转义点行逐行复现(fuse 3→3),SectionLocator 0 误升(修复在新数据成立);QC 0 issue"),
    "pac-c12-02": ("深度", "PASS", "BUG-25 台账卷:L445/L461 转义点行复现(esc_dot 2→2),0 误升;P13×4 为紧凑答案行/答案即解析格式盲区(答案内容在,绑定正确);QC 0 issue"),
    "pac-c13-01": ("深度", "PASS", "覆盖 34/34(19 单元);语义探针 0 报警;复合题整块化正确"),
    "pac-c13-02": ("深度", "PASS", "覆盖 20/20;P15×5 实查:Q20=二选一作文(题干区『六、本大题共1小题』),尾部解析两条恰对应两个选项,但解析区自称『共2小题』且编号 10/11——**源卷题干区与答案区版本不一致**(如实反映;printed=None 未伪造;绑定语义正确;resolver 消费须知 answer 区编号可与题干区不一致)"),
}


def load(p):
    return json.loads((ROOT / p).read_text(encoding="utf-8"))


def main():
    sel = load("data/pac_selection.json")
    ocr = load("data/pac_track_ocr.json")
    ann = {Path(r["file"]).stem: r for r in load("data/reslice_reslice-pac-annotated_result.json")}
    qc = {Path(r["file"]).stem: r for r in load("data/pac_qc_v2.json")}
    bf = {Path(r["file"]).stem: r for r in load("data/pac_identity_backfill_report.json")["files"]}

    tracks = []
    for s in sel["samples"]:
        sid = s["sample_id"]
        man = json.loads((OUT_DIR / f"{sid}.manifest.json").read_text(encoding="utf-8"))
        a, q = ann[sid], qc[sid]
        method, verdict, notes = REVIEW[sid]
        tracks.append({
            "sample_id": sid,
            "category": s["category"],
            "hazard_evidence": s["hazard_evidence"],
            "stages": {
                "source":     {"status": "OK", "pdf_sha256": s["pdf"]["sha256"],
                               "pages": s["pdf"]["pages"], "text_layer": s["pdf"]["text_layer"]},
                "ocr":        {k: ocr[sid].get(k) for k in
                               ("status", "job_id", "pages_billed", "duration_s", "output_md_sha256")},
                "annotation": {"status": "FAIL" if a.get("error") else "OK",
                               "model": "mimo-x-pro-preview",
                               "prompt_tokens": a.get("prompt_tokens"),
                               "completion_tokens": a.get("completion_tokens"),
                               "elapsed_s": a.get("elapsed_s"),
                               "validation_issues": a.get("issues") or []},
                "manifest":   {"status": "OK", "units": len(man["units"]),
                               "identity_version": man.get("identity_version"),
                               "sections": len(man.get("sections") or [])},
                "qc":         {"status": "OK", "verdict": q["verdict"], "issues": q["issues"]},
                "identity":   {"status": "OK", "backfilled": bf[sid]["applied"],
                               "fails": len(bf[sid]["fail_issues"]),
                               "reviews": len(bf[sid]["review_notes"])},
                "artifact":   {"status": "OK", "dir": str(OUT_DIR / sid)},
                "resolver":   {"status": "NOT_BUILT"},
                "compiler":   {"status": "NOT_BUILT"},
                "gate":       {"status": "NOT_BUILT"},
                "admission":  {"status": "NOT_BUILT"},
            },
            "human_review": {"method": method, "verdict": verdict, "notes": notes},
        })

    out = {"round": 1, "date": "2026-09-13", "n": len(tracks),
           "qc_pass": sum(1 for t in tracks if t["stages"]["qc"]["verdict"] == "PASS"),
           "qc_fail": sum(1 for t in tracks if t["stages"]["qc"]["verdict"] == "FAIL"),
           "tracks": tracks}
    p = ROOT / "data/pac_track_round1.json"
    p.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8", newline="")
    print(f"留档 {p}:QC {out['qc_pass']} PASS / {out['qc_fail']} FAIL")


if __name__ == "__main__":
    main()
