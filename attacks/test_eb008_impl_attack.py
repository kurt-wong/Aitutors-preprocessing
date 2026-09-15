"""DSH EB-008 Implementation Adversarial Review — 四域攻击套件(实现验收,非设计审查)。

攻击基线:V3 commit 88aeae8(实现)+ b5ddbe3(实现说明)。
判据:EB008-DSH-IMPL-ACCEPTANCE.md 四验收域 A/B/C/D(DEC-018 冻结)。
哲学:证明"坏的 Evidence 进不去",而非"好的能进去"。

标注约定:
- 正常攻击用例 = 攻击必须被拒(断言异常 + 状态不变 + 无 Question 物化)。
- FINDING 演证用例 = 攻击成功复现,用于实锤残余风险并分类定级。
"""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import select, text
from sqlalchemy import func

from app.domains.evidence.models import CheckResult, ValidationEvent
from app.domains.evidence.proof import (
    generate_review_proof,
    human_validator,
    verify_review_proof,
)
from app.domains.gate.admission import AdmissionService
from app.domains.gate.service import GateService
from app.models.content import Question
from app.models.evidence import ValidationEventRecord
from app.models.snapshot import AdmissionCandidate
from app.repositories.base import RepositoryError
from app.repositories.evidence_repository import EvidenceRepository
from app.repositories.snapshot_repository import SnapshotRepository
from tests.eb008_helpers import (
    CLAIM_ID,
    auto_gate_decision,
    pending_gate_decision,
    seed_candidate,
    seed_validated_authority,
)
from tests.test_admission import (
    _auto_gd,
    _counts,
    _dummy_payload,
    _make_candidate,
    _pending_gd,
)
from tests.test_gate_service import _seed as _gate_seed

UTC = timezone.utc


async def _fresh_candidate(session, sv, ann, gate):
    """完整物化结构 candidate(可过 approve 物化路径)。"""
    cand = await _make_candidate(session, sv, ann, gate)
    await session.flush()
    return cand


async def _plant_human_event(session, cand, sv, *, claim_id="Q1",
                             review_result="validated", secret=None):
    """生产等价的 human_review 事件 + 合法 proof(模拟 _record_human_review 落库结果)。"""
    reviewed_at = datetime.now(UTC)
    proof = generate_review_proof(
        candidate_id=cand.id, review_result=review_result,
        reviewer_id="owner", reviewed_at=reviewed_at, app_secret=secret,
    )
    rec = await EvidenceRepository(session).append_human_review_event(
        candidate_id=cand.id, source_version_id=sv.id, claim_id=claim_id,
        review_result=review_result, reviewer_id="owner",
        reviewed_at=reviewed_at, review_proof=proof,
    )
    await session.flush()
    return rec


async def _sql_update(session, sql: str, **params) -> None:
    """DB 直连 UPDATE 攻击(R-3 能力模型内;proof 声明 2 的对抗面)。

    populate_existing 刷新:绕开 ORM identity map 陈旧值,后续读取反映 DB 直改后的
    真实值(等价"新进程读库",避免测试假象);刷新发生在 await 上下文内,不触发
    MissingGreenlet。
    """
    await session.execute(text(sql), params)
    await session.flush()
    await session.execute(
        select(ValidationEventRecord).execution_options(populate_existing=True)
    )


# ===================================================================
# A. Identity —— 同 hash 复用 / replay / 身份因素纯度
# ===================================================================
class TestAttackIdentity:
    async def test_a1_same_input_repeat_gate_same_candidate_authority(self, session):
        """同输入重复 Gate:candidate 复用(le_hash 幂等)、事件恰 1 行、Authority 不变。"""
        sv, ann = await _gate_seed(session)
        c1, _ = await GateService(session).run(
            source_version_id=sv.id, annotation_id=ann.id
        )
        await session.flush()
        repo = EvidenceRepository(session)
        claim = c1[0].payload["ir_snapshot"]["units"][0]["unit_id"]
        state_1, latest_1 = await repo.project_authority(c1[0].id, claim)

        c2, _ = await GateService(session).run(
            source_version_id=sv.id, annotation_id=ann.id
        )
        await session.flush()
        events = await repo.find_events_for_candidate(c1[0].id)
        state_2, latest_2 = await repo.project_authority(c1[0].id, claim)

        assert c1[0].id == c2[0].id, "同输入必须复用同一 candidate(le_hash 幂等)"
        assert len(events) == 1, "replay 不得新增 validation_events 行"
        assert state_1 == state_2 == "validated"
        assert latest_1.id == latest_2.id

    async def test_a2_cross_run_replay_new_session_authority_stable(self, session):
        """不同 Run(新 session/新 GateService 实例,已 COMMIT)replay:
        同 candidate、同 Authority 投影(持久化,非内存)。"""
        from app.db.session import async_session_maker

        sv, ann = await _gate_seed(session)
        c1, _ = await GateService(session).run(
            source_version_id=sv.id, annotation_id=ann.id
        )
        claim = c1[0].payload["ir_snapshot"]["units"][0]["unit_id"]
        cand_id = c1[0].id
        doc_id = sv.document_id
        sv_id = sv.id
        await session.commit()  # Run-1 落库(模拟进程结束)
        try:
            async with async_session_maker() as s2:  # Run-2:全新 session
                c2, _ = await GateService(s2).run(
                    source_version_id=sv.id, annotation_id=ann.id
                )
                await s2.flush()
                repo2 = EvidenceRepository(s2)
                events = await repo2.find_events_for_candidate(cand_id)
                state, latest = await repo2.project_authority(cand_id, claim)
                assert c2[0].id == cand_id, "跨 Run 同 hash 必须命中同一 candidate"
                assert len(events) == 1, "跨 Run replay 不得新增事件行"
                assert state == "validated"
                await s2.rollback()
        finally:
            async with async_session_maker() as sc:
                qids = (await sc.execute(
                    text("SELECT created_question_ids FROM admission_events "
                         "WHERE candidate_id=CAST(:c AS uuid)"),
                    {"c": cand_id},
                )).scalar() or []
                for sql, p in (
                    ("DELETE FROM unit_group_members WHERE unit_group_id IN "
                     "(SELECT id FROM unit_groups WHERE source_version_id=CAST(:s AS uuid))",
                     {"s": sv_id}),
                    ("DELETE FROM unit_group_members WHERE instance_id IN "
                     "(SELECT id FROM question_instances WHERE source_version_id=CAST(:s AS uuid))",
                     {"s": sv_id}),
                    ("DELETE FROM material_links WHERE instance_id IN "
                     "(SELECT id FROM question_instances WHERE source_version_id=CAST(:s AS uuid))",
                     {"s": sv_id}),
                    ("DELETE FROM instance_figure_links WHERE instance_id IN "
                     "(SELECT id FROM question_instances WHERE source_version_id=CAST(:s AS uuid))",
                     {"s": sv_id}),
                    ("DELETE FROM instance_role_contents WHERE instance_id IN "
                     "(SELECT id FROM question_instances WHERE source_version_id=CAST(:s AS uuid))",
                     {"s": sv_id}),
                    ("DELETE FROM question_instances WHERE source_version_id=CAST(:s AS uuid)",
                     {"s": sv_id}),
                    ("DELETE FROM unit_groups WHERE source_version_id=CAST(:s AS uuid)",
                     {"s": sv_id}),
                    ("DELETE FROM materials WHERE source_version_id=CAST(:s AS uuid)",
                     {"s": sv_id}),
                    ("DELETE FROM admission_events WHERE candidate_id=CAST(:c AS uuid)",
                     {"c": cand_id}),
                    ("DELETE FROM validation_events WHERE candidate_id=CAST(:c AS uuid)",
                     {"c": cand_id}),
                    ("DELETE FROM admission_candidates WHERE id=CAST(:c AS uuid)",
                     {"c": cand_id}),
                    ("DELETE FROM semantic_annotations WHERE source_version_id=CAST(:s AS uuid)",
                     {"s": sv_id}),
                    ("DELETE FROM document_source_lines WHERE source_version_id=CAST(:s AS uuid)",
                     {"s": sv_id}),
                    ("DELETE FROM document_source_versions WHERE id=CAST(:s AS uuid)",
                     {"s": sv_id}),
                    ("DELETE FROM documents WHERE id=CAST(:d AS uuid)", {"d": doc_id}),
                ):
                    await sc.execute(text(sql), p)
                for q in qids:
                    await sc.execute(
                        text("DELETE FROM question_knowledge_links "
                             "WHERE question_id=CAST(:q AS uuid)"), {"q": str(q)})
                    await sc.execute(
                        text("DELETE FROM questions WHERE id=CAST(:q AS uuid)"),
                        {"q": str(q)})
                await sc.commit()

    async def test_a3_attempt_id_not_in_identity(self, session):
        """I6:attempt_id(Runtime Provenance)不进身份 —— 不同 attempt_id 重跑必须复用 candidate。"""
        sv, ann = await _gate_seed(session)
        c1, _ = await GateService(session).run(
            source_version_id=sv.id, annotation_id=ann.id, attempt_id=uuid.uuid4()
        )
        c2, _ = await GateService(session).run(
            source_version_id=sv.id, annotation_id=ann.id, attempt_id=uuid.uuid4()
        )
        await session.flush()
        assert c1[0].id == c2[0].id, "attempt_id 不得进入 le_hash 身份"

    async def test_a4_le_hash_inputs_contain_no_nondentity_factors(self, session):
        """le_hash 输入域审计:无 run_id/attempt_id/time/created 类字段。"""
        sv, ann = await _gate_seed(session)
        input_domain = GateService._compile_input_domain(ann.id, ann, "U1")
        contract_domain = GateService._compile_contract_domain()
        assert set(input_domain) == {
            "annotation_id", "annotation_payload_hash", "unit_id"
        }
        assert set(contract_domain) == {
            "resolver_version", "ir_schema_version",
            "compiler_version", "gate_policy_version",
        }
        for key in list(input_domain) + list(contract_domain):
            assert not any(
                bad in key.lower()
                for bad in ("run", "attempt", "time", "created", "timestamp")
            ), f"非身份因素 {key!r} 混入 le_hash 输入"
        h1 = GateService._compile_input_domain(ann.id, ann, "U1")
        assert h1 == input_domain, "同输入跨时计算必须同 hash(时间不进 hash)"

    async def test_a5_claim_id_gate_and_boundary_same_source(self, session):
        """claim_id 同源:Gate 落库的 claim == Admission enforcement 解析的 claim(payload units[0])。"""
        from app.domains.gate.admission import _candidate_claim_id

        sv, ann = await _gate_seed(session)
        c1, _ = await GateService(session).run(
            source_version_id=sv.id, annotation_id=ann.id
        )
        await session.flush()
        cand = c1[0]
        events = await EvidenceRepository(session).find_events_for_candidate(cand.id)
        assert events, "Gate 必须落事件"
        assert events[0].claim_id == _candidate_claim_id(cand), \
            "Gate 落库 claim 与 Boundary 解析 claim 必须同源"


# ===================================================================
# B. Human Proof —— 篡改/删除/伪造全部 fail-closed
# ===================================================================
class TestAttackHumanProof:
    async def _pending_human_setup(self, session, gate=None):
        sv, ann, _ = await seed_candidate(
            session, gate=gate or pending_gate_decision()
        )
        snap = SnapshotRepository(session)
        cand = await snap.create_admission_candidate(
            unit_type="standalone_unit", source_version_id=sv.id,
            annotation_id=ann.id, build_versions={"v": "1"}, input_identity={},
            payload=_dummy_payload(), gate_decision=gate or _pending_gd(),
            logical_execution_stage="compile",
            logical_execution_hash=uuid.uuid4().hex,
        )
        await session.flush()
        await snap.append_review_trail(cand.id, {
            "decision": "approve", "verified_by": "human", "reviewer_id": "owner",
        })
        await session.flush()
        return sv, ann, cand

    async def test_b1a_tamper_validated_at_proof_invalid_blocked(self, session):
        """SQL 直改 validated_at(状态不变)→ proof 重算失配 → approve 被拒。"""
        sv, _ann, cand = await self._pending_human_setup(session)
        rec = await _plant_human_event(session, cand, sv)
        await _sql_update(
            session,
            "UPDATE validation_events SET validated_at = validated_at "
            "- interval '1 hour' WHERE id = CAST(:i AS uuid)",
            i=str(rec.id),
        )
        with pytest.raises(RepositoryError, match="proof invalid"):
            await AdmissionService(session).approve(
                candidate_id=cand.id,
                provenance={"source": "human", "reviewer_id": "owner"},
            )
        row = await session.get(AdmissionCandidate, cand.id)
        assert row.decision_status == "pending_review"
        assert await _counts(session, Question) == 0, "被拒后不得物化 Question"

    async def test_b1b_tamper_review_result_two_layers_block(self, session):
        """SQL 直改 review_result:①verify_review_proof=False(声明 2);
        ②approve 双重被拒(状态机 terminal + proof 失败)。"""
        sv, _ann, cand = await self._pending_human_setup(session)
        rec = await _plant_human_event(session, cand, sv)
        await _sql_update(
            session,
            "UPDATE validation_events SET validation_result='rejected' "
            "WHERE id = CAST(:i AS uuid)",
            i=str(rec.id),
        )
        tampered = await session.get(ValidationEventRecord, rec.id)
        assert verify_review_proof(tampered) is False, "改 review_result 必须验证失败"
        with pytest.raises((RepositoryError, ValueError)):
            await AdmissionService(session).approve(
                candidate_id=cand.id,
                provenance={"source": "human", "reviewer_id": "owner"},
            )
        row = await session.get(AdmissionCandidate, cand.id)
        assert row.decision_status == "pending_review"
        assert await _counts(session, Question) == 0

    async def test_b2_tamper_candidate_id_rebind_blocks_auto(self, session):
        """SQL 改事件 candidate_id(重绑):原 candidate Authority=none → auto approve 被拒。"""
        sv, ann, _ = await seed_candidate(session)
        cand = await _fresh_candidate(session, sv, ann, _auto_gd())
        await seed_validated_authority(session, cand, sv)
        sv2, ann2, _ = await seed_candidate(session)
        other = await _fresh_candidate(session, sv2, ann2, _auto_gd())
        await session.flush()
        await _sql_update(
            session,
            "UPDATE validation_events SET candidate_id = CAST(:o AS uuid) "
            "WHERE candidate_id = CAST(:c AS uuid)",
            o=str(other.id), c=str(cand.id),
        )
        with pytest.raises(RepositoryError, match="fail-closed"):
            await AdmissionService(session).approve(
                candidate_id=cand.id, provenance={"source": "auto_gate"}
            )
        row = await session.get(AdmissionCandidate, cand.id)
        assert row.decision_status == "pending_review"

    async def test_b3_delete_proof_sql_blocked(self, session):
        """SQL 删 proof(NULL 化):replay no-op 返回既有行 → verify False → approve 被拒。"""
        sv, _ann, cand = await self._pending_human_setup(session)
        rec = await _plant_human_event(session, cand, sv)
        await _sql_update(
            session,
            "UPDATE validation_events SET review_proof = NULL "
            "WHERE id = CAST(:i AS uuid)",
            i=str(rec.id),
        )
        with pytest.raises(RepositoryError, match="proof invalid"):
            await AdmissionService(session).approve(
                candidate_id=cand.id,
                provenance={"source": "human", "reviewer_id": "owner"},
            )
        row = await session.get(AdmissionCandidate, cand.id)
        assert row.decision_status == "pending_review"
        assert await _counts(session, Question) == 0

    async def test_b4_forge_proof_wrong_secret_blocked(self, session):
        """伪造 human_review 事件(攻击者自算 proof,无真 APP_SECRET):verify False → 被拒。"""
        sv, ann, _ = await seed_candidate(session)
        cand = await _fresh_candidate(session, sv, ann, _auto_gd())
        await session.flush()
        forged_proof = generate_review_proof(
            candidate_id=cand.id, review_result="validated",
            reviewer_id="owner", reviewed_at=datetime.now(UTC),
            app_secret="attacker-guessed-secret-32-bytes-long!!",
        )
        # 绕过唯一写入口,直插 ORM 行(等价 DB 直连 INSERT)
        session.add(ValidationEventRecord(
            claim_id=CLAIM_ID, candidate_id=cand.id, source_version_id=sv.id,
            validation_result="validated", checks=[],
            validation_method="human_review", validator=human_validator("owner"),
            review_proof=forged_proof, validated_at=datetime.now(UTC),
        ))
        await session.flush()
        with pytest.raises(RepositoryError, match="proof invalid"):
            await AdmissionService(session).approve(
                candidate_id=cand.id, provenance={"source": "auto_gate"}
            )
        row = await session.get(AdmissionCandidate, cand.id)
        assert row.decision_status == "pending_review"

    async def test_b5_missing_app_secret_fails_closed(self, session, monkeypatch):
        """APP_SECRET 置空:human approve 路径必须抛错(fail-closed,不 fail-open)。"""
        from app.core.config import settings

        sv, _ann, cand = await self._pending_human_setup(session)
        monkeypatch.setattr(settings, "app_secret", "")
        with pytest.raises(RepositoryError, match="APP_SECRET"):
            await AdmissionService(session).approve(
                candidate_id=cand.id,
                provenance={"source": "human", "reviewer_id": "owner"},
            )
        row = await session.get(AdmissionCandidate, cand.id)
        assert row.decision_status == "pending_review"

    async def test_b6_finding_method_laundering_bypass(self, session):
        """[FINDING 演证] DB 直连把 human_review 行洗成 machine 外观
        (validation_method='byte_proven' + validator='gate/v1' + proof=NULL):
        proof 校验被跳过 → approve 成功物化。
        分类依据:R-3(DB 直连 = Deployment Boundary)+ 声明 2 只承诺
        review_result/proof-replay 两类篡改检测;此向量 = 残余风险,非实现偏离。"""
        sv, _ann, cand = await self._pending_human_setup(session)
        rec = await _plant_human_event(session, cand, sv)
        await _sql_update(
            session,
            "UPDATE validation_events SET validation_method='byte_proven', "
            "validator='gate/v1', review_proof=NULL WHERE id = CAST(:i AS uuid)",
            i=str(rec.id),
        )
        decided = await AdmissionService(session).approve(
            candidate_id=cand.id,
            provenance={"source": "human", "reviewer_id": "owner"},
        )
        assert decided.decision_status == "approved", \
            "预期实锤:method 洗白绕过 proof 校验(DB 直连能力,R-3 边界)"


# ===================================================================
# C. Admission Boundary —— P3.2 N1/N2/N7/N8 复跑 + 双入口
# ===================================================================
class TestAttackAdmissionBoundary:
    async def test_c1_n1_claim_without_event_blocked(self, session):
        """N1 复跑(EvidenceClaim 在,无 ValidationEvent):approve 被拒,无物化。"""
        sv, ann, _ = await seed_candidate(session)
        cand = await _fresh_candidate(session, sv, ann, _auto_gd())
        await session.flush()
        with pytest.raises(RepositoryError, match="fail-closed"):
            await AdmissionService(session).approve(
                candidate_id=cand.id, provenance={"source": "auto_gate"}
            )
        row = await session.get(AdmissionCandidate, cand.id)
        assert row.decision_status == "pending_review"
        assert await _counts(session, Question) == 0

    async def test_c2_n2_invalid_result_event_blocked(self, session):
        """N2 复跑(ValidationEvent 在但结果非法,raw INSERT 绕过 domain 值域):
        投影 state!='validated' → approve 被拒。"""
        sv, ann, _ = await seed_candidate(session)
        cand = await _fresh_candidate(session, sv, ann, _auto_gd())
        await session.flush()
        session.add(ValidationEventRecord(
            claim_id=CLAIM_ID, candidate_id=cand.id, source_version_id=sv.id,
            validation_result="maybe", checks=[],
            validation_method="frozen_header_rule", validator="gate/v1",
            validated_at=datetime.now(UTC),
        ))
        await session.flush()
        with pytest.raises(RepositoryError, match="fail-closed"):
            await AdmissionService(session).approve(
                candidate_id=cand.id, provenance={"source": "auto_gate"}
            )
        row = await session.get(AdmissionCandidate, cand.id)
        assert row.decision_status == "pending_review"
        assert await _counts(session, Question) == 0

    async def test_c3_n7_direct_admission_bypassing_promotion_blocked(self, session):
        """N7 复跑(核心):绕过 GateService/promotion 直连 AdmissionService.approve ——
        FACT-021 基线 = BYPASS,现要求 = BLOCKED。"""
        sv, ann, _ = await seed_candidate(session)
        cand = await _fresh_candidate(session, sv, ann, _auto_gd())
        await session.flush()
        with pytest.raises(RepositoryError, match="fail-closed"):
            await AdmissionService(session).approve(
                candidate_id=cand.id, provenance={"source": "auto_gate"}
            )
        assert await _counts(session, Question) == 0
        row = await session.get(AdmissionCandidate, cand.id)
        assert row.decision_status == "pending_review"

    async def test_c4_n8_gate_approve_authority_invalid_blocked(self, session):
        """N8 复跑(核心):gate_decision=auto_approve 但 Authority=REJECTED → BLOCKED。"""
        sv, ann, _ = await seed_candidate(session)
        cand = await _fresh_candidate(session, sv, ann, _auto_gd())
        await EvidenceRepository(session).append_event(
            ValidationEvent(
                event_id=f"ve-{uuid.uuid4().hex[:8]}", claim_id=CLAIM_ID,
                validation_result="rejected", checks=(),
                validation_method="structural_consistency", validator="gate/v1",
            ),
            candidate_id=cand.id, source_version_id=sv.id,
        )
        await session.flush()
        with pytest.raises(RepositoryError, match="fail-closed"):
            await AdmissionService(session).approve(
                candidate_id=cand.id, provenance={"source": "auto_gate"}
            )
        row = await session.get(AdmissionCandidate, cand.id)
        assert row.decision_status == "pending_review"
        assert await _counts(session, Question) == 0

    async def test_c5_invalidated_blocks_human_approve(self, session):
        """INVALIDATED 后 human 路径 approve:terminal 状态机拒新事件 → 物化不发生。"""
        sv, ann, _ = await seed_candidate(session)
        cand = await _fresh_candidate(session, sv, ann, _pending_gd())
        snap = SnapshotRepository(session)
        await snap.append_review_trail(cand.id, {
            "decision": "approve", "verified_by": "human", "reviewer_id": "owner",
        })
        await seed_validated_authority(session, cand, sv)
        await EvidenceRepository(session).append_event(
            ValidationEvent(
                event_id=f"ve-{uuid.uuid4().hex[:8]}", claim_id=CLAIM_ID,
                validation_result="invalidated", checks=(),
                validation_method="structural_consistency", validator="system/v1",
                validated_at=datetime.now(UTC) + timedelta(seconds=1),
            ),
            candidate_id=cand.id, source_version_id=sv.id,
        )
        await session.flush()
        with pytest.raises((RepositoryError, ValueError)):
            await AdmissionService(session).approve(
                candidate_id=cand.id,
                provenance={"source": "human", "reviewer_id": "owner"},
            )
        row = await session.get(AdmissionCandidate, cand.id)
        assert row.decision_status == "pending_review"
        assert await _counts(session, Question) == 0

    async def test_c6_human_approve_without_trail_blocked(self, session):
        """双入口纪律:human 路径无 review_trail 人工 entry → 拒(20 §8.2)。"""
        sv, ann, _ = await seed_candidate(session)
        cand = await _fresh_candidate(session, sv, ann, _pending_gd())
        with pytest.raises(RepositoryError, match="review_trail"):
            await AdmissionService(session).approve(
                candidate_id=cand.id,
                provenance={"source": "human", "reviewer_id": "owner"},
            )
        assert await _counts(session, Question) == 0


# ===================================================================
# D. Lifecycle —— invalidate / replay / Authority 不复活
# ===================================================================
class TestAttackLifecycle:
    async def test_d1_validated_to_invalidated_blocks_approve(self, session):
        """VALIDATED →(annotation supersede 级联)→ INVALIDATED → approve 被拒。"""
        sv, ann, _ = await seed_candidate(session)
        cand = await _fresh_candidate(session, sv, ann, _auto_gd())
        await seed_validated_authority(session, cand, sv)
        await SnapshotRepository(session).set_annotation_status(ann.id, "superseded")
        await session.flush()
        state, _ = await EvidenceRepository(session).project_authority(
            cand.id, CLAIM_ID
        )
        assert state == "invalidated"
        with pytest.raises(RepositoryError, match="fail-closed"):
            await AdmissionService(session).approve(
                candidate_id=cand.id, provenance={"source": "auto_gate"}
            )
        assert await _counts(session, Question) == 0

    async def test_d2_gate_rerun_after_invalidate_no_resurrection(self, session):
        """INVALIDATED 后重跑 Gate(replay):Authority 不得复活,不得 approve。"""
        sv, ann = await _gate_seed(session)
        c1, _ = await GateService(session).run(
            source_version_id=sv.id, annotation_id=ann.id
        )
        await session.flush()
        await SnapshotRepository(session).set_annotation_status(ann.id, "superseded")
        await session.flush()
        try:
            await GateService(session).run(
                source_version_id=sv.id, annotation_id=ann.id
            )
        except Exception:
            pass  # 上游 binding/状态机任一层拒绝均可 —— 判据是下方不变式
        await session.flush()
        repo = EvidenceRepository(session)
        claim = c1[0].payload["ir_snapshot"]["units"][0]["unit_id"]
        state, _ = await repo.project_authority(c1[0].id, claim)
        assert state == "invalidated", "Gate replay 不得复活 Authority"
        events = await repo.find_events_for_claim(c1[0].id, claim)
        validated_rows = [
            e for e in events
            if e.validation_result == "validated"
            and e.validated_at > max(x.validated_at for x in events
                                     if x.validation_result == "invalidated")
        ]
        assert not validated_rows, "不得出现晚于 INVALIDATED 的 VALIDATED 行"
        # NOTE:invalidate 不回溯撤销 run-1 已完成的 approve/物化(冻结设计只规定
        # Authority 状态与后续 approve 拒绝,未含 retroactive un-materialization)。
        # 此处只验证:重跑未产生任何新的 approve/物化,Authority 不复活。
        row = await session.get(AdmissionCandidate, c1[0].id)
        events_all = await repo.find_events_for_candidate(c1[0].id)
        assert all(
            e.validation_result != "validated"
            for e in events_all
            if e.validated_at
            > max(x.validated_at for x in events_all
                  if x.validation_result == "invalidated")
        ), "replay 之后不得出现新的 VALIDATED 事件"

    async def test_d3_double_invalidate_idempotent(self, session):
        """重复 invalidate:第二次级联为空,事件行数不变,Authority 保持 INVALIDATED。"""
        sv, ann, cand = await seed_candidate(session)
        await seed_validated_authority(session, cand, sv)
        repo = EvidenceRepository(session)
        first = await repo.invalidate_claims_for_annotation(
            ann.id, reason="supersede-1"
        )
        assert len(first) == 1
        second = await repo.invalidate_claims_for_annotation(
            ann.id, reason="supersede-2"
        )
        assert second == [], "重复 invalidate 不得新增事件"
        events = await repo.find_events_for_claim(cand.id, CLAIM_ID)
        assert len(events) == 2  # validated + invalidated,恰各一行
        state, _ = await repo.project_authority(cand.id, CLAIM_ID)
        assert state == "invalidated"

    async def test_d4_replay_same_result_after_invalidate_noop(self, session):
        """INVALIDATED 后同结果重放:replay no-op,不新增行,不复活。"""
        sv, ann, cand = await seed_candidate(session)
        await seed_validated_authority(session, cand, sv)
        repo = EvidenceRepository(session)
        inv = await repo.invalidate_claims_for_annotation(ann.id, reason="x")
        again = await repo.append_event(
            ValidationEvent(
                event_id=f"ve-{uuid.uuid4().hex[:8]}", claim_id=CLAIM_ID,
                validation_result="invalidated", checks=(),
                validation_method="structural_consistency", validator="system/v1",
            ),
            candidate_id=cand.id, source_version_id=sv.id,
        )
        assert again.id == inv[0].id, "同结果重放必须 no-op 返回既有行"
        events = await repo.find_events_for_claim(cand.id, CLAIM_ID)
        assert len(events) == 2
        state, _ = await repo.project_authority(cand.id, CLAIM_ID)
        assert state == "invalidated"

    async def test_d5_finding_future_timestamp_resurrection_latent(self, session):
        """[FINDING 演证] latest-by-validated_at 排序的潜在复活面:
        未来时间戳 VALIDATED 事件使 cascade 的 INVALIDATED(now)不是 latest →
        投影回 VALIDATED → approve 成功。
        生产暴露面核查:机器事件=服务端 utcnow(promotion.py),人工事件=append_review_trail
        服务端注入 time,cascade=now —— 当前无任何生产路径接受调用方时间输入,
        该向量需要 raw/未来 bug 才能构造;定级 WARNING(潜在),不构成当前 BYPASS。"""
        sv, ann, _ = await seed_candidate(session)
        cand = await _fresh_candidate(session, sv, ann, _auto_gd())
        future = datetime.now(UTC) + timedelta(hours=1)
        repo = EvidenceRepository(session)
        await repo.append_event(
            ValidationEvent(
                event_id=f"ve-{uuid.uuid4().hex[:8]}", claim_id=CLAIM_ID,
                validation_result="validated", checks=(),
                validation_method="frozen_header_rule", validator="gate/v1",
                validated_at=future,  # 应用层 API 可传 —— 生产调用方均不传
            ),
            candidate_id=cand.id, source_version_id=sv.id,
        )
        created = await repo.invalidate_claims_for_annotation(
            ann.id, reason="supersede"
        )
        assert len(created) == 1, "cascade 已写入 INVALIDATED"
        state, _ = await repo.project_authority(cand.id, CLAIM_ID)
        assert state == "validated", \
            "预期实锤:未来时间戳使 INVALIDATED 不是 latest,投影复活"
        decided = await AdmissionService(session).approve(
            candidate_id=cand.id, provenance={"source": "auto_gate"}
        )
        assert decided.decision_status == "approved", \
            "预期实锤:复活后的 Authority 放行 approve(潜在风险演证)"
