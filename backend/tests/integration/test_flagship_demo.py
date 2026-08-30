# backend/tests/integration/test_flagship_demo.py
"""
End-to-End Integration Tests for Phase 6 Flagship Demo
Validates the complete multi-modal industrial inspection workflow:
- Ingestion of 5 heterogeneous engineering assets
- FastEmbed + Qdrant dense vector search for NDT & OEM manual tolerances
- Micro-isolated Docker sandbox Python execution with linear regression
- Engineering Approval Note DOCX artifact generation
- Cryptographic continuous SHA-256 audit ledger verification
"""

import asyncio
from pathlib import Path
import pytest
from sqlalchemy.orm import Session

from backend.app.core.audit_logger import AuditLogger
from backend.app.core.security import generate_uuid
from backend.app.db.models.workspace_orm import WorkspaceORM
from backend.app.ingestion.pipeline import DocumentIngestionPipeline
from backend.app.rag.embeddings import LocalEmbeddingEngine
from backend.app.rag.vector_store import QdrantVectorStore
from backend.app.agent.sandbox.manager import SandboxManager
from backend.app.agent.tools.run_python import RunPythonTool, RunPythonInput
from backend.app.agent.tools.generate_docx import GenerateDocxTool, GenerateDocxInput, FindingRow

DEMO_ASSETS_DIR = Path(__file__).resolve().parent.parent.parent.parent / "demo" / "assets"


@pytest.mark.asyncio
async def test_flagship_demo_end_to_end_flow(db_session: Session, tmp_path: Path):
    """
    Test complete Phase 6 industrial inspection pipeline from ingestion to artifact delivery.
    """
    from backend.app.config import settings
    orig_workspaces_dir = settings.WORKSPACES_DIR
    settings.WORKSPACES_DIR = tmp_path / "workspaces"

    try:
        # 1. Setup isolated workspace
        ws_id = generate_uuid("ws")
        ws_dir = tmp_path / "workspaces" / ws_id
        ws_dir.mkdir(parents=True, exist_ok=True)
        artifacts_dir = ws_dir / "artifacts"
        artifacts_dir.mkdir(parents=True, exist_ok=True)

        workspace = WorkspaceORM(
            id=ws_id,
            name="Reflux Pump 3B Flagship Test Workspace",
            description="E2E test of multi-modal industrial inspection package",
            classification_level="INTERNAL_ENGINEERING",
            storage_path=str(ws_dir)
        )
        db_session.add(workspace)
        db_session.commit()

        # 2. Stage the 5 assets
        assert DEMO_ASSETS_DIR.exists(), "demo/assets directory missing!"
        rag_assets = [
            "inspection_report.pdf",
            "scanned_report.pdf",
            "maintenance_history.xlsx",
            "maintenance_manual.pdf",
        ]
        all_assets = rag_assets + ["equipment_photo.jpg"]

        for fname in all_assets:
            src = DEMO_ASSETS_DIR / fname
            assert src.exists(), f"Demo asset {fname} not found!"
            dst = ws_dir / fname
            dst.write_bytes(src.read_bytes())

        # 3. Ingest documents into Vector Store
        embedder = LocalEmbeddingEngine.get_instance()
        mem_vector_store = QdrantVectorStore(location=":memory:")
        mem_vector_store.init_collection(dimension=embedder.dimension, recreate=True)

        pipeline = DocumentIngestionPipeline(
            vector_store=mem_vector_store,
            embedding_engine=embedder
        )

        for fname in rag_assets:
            doc_orm = pipeline.ingest_file(
                session=db_session,
                workspace_id=ws_id,
                relative_path=fname,
                classification="INTERNAL_ENGINEERING",
                enable_ocr=True
            )
            assert doc_orm.parsing_status == "INDEXED"
            assert doc_orm.page_count >= 1

        # 4. Query NDT thickness measurement
        query_vec = embedder.embed_query("Pump 3B ultrasonic wall thickness measurements node C-12")
        ndt_hits = mem_vector_store.search(
            query_vector=query_vec,
            workspace_id=ws_id,
            top_k=2
        )
        assert len(ndt_hits) > 0
        assert "inspection_report.pdf" in ndt_hits[0]["filename"]
        assert "3.42" in ndt_hits[0]["content"]

        # 5. Query OEM replacement tolerance
        manual_vec = embedder.embed_query("Pump 3B minimum allowable shell thickness replacement limit Table 8.4")
        manual_hits = mem_vector_store.search(
            query_vector=manual_vec,
            workspace_id=ws_id,
            top_k=2
        )
        assert len(manual_hits) > 0
        assert "maintenance_manual.pdf" in manual_hits[0]["filename"]
        assert "4.00" in manual_hits[0]["content"]

        # 6. Execute Python regression in Docker sandbox
        sandbox_mgr = SandboxManager()
        docker_ok, _ = sandbox_mgr.check_docker_available()
        if docker_ok:
            run_python_tool = RunPythonTool(sandbox_manager=sandbox_mgr)
            python_script = (
                "import pandas as pd\n"
                "import numpy as np\n\n"
                "df = pd.read_excel('/workspace/input/maintenance_history.xlsx', sheet_name='Thickness_Log')\n"
                "p3b = df[df['Component'] == 'Pump_3B_Casing']\n"
                "years = p3b['Year'].values\n"
                "thickness = p3b['Thickness_mm'].values\n"
                "rate = -np.polyfit(years, thickness, 1)[0]\n"
                "print(f'Historical Thinning Rate: {rate:.3f} mm/year')\n"
            )
            sandbox_res = await run_python_tool.execute(
                workspace_id=ws_id,
                input_data=RunPythonInput(script=python_script, timeout_seconds=15)
            )
            assert sandbox_res.exit_code == 0
            assert "Historical Thinning Rate:" in sandbox_res.stdout

        # 7. Generate DOCX artifact
        docx_tool = GenerateDocxTool()
        docx_input = GenerateDocxInput(
            output_filename="Engineering_Approval_Note_Pump3B.docx",
            title="ENGINEERING APPROVAL NOTE — REFLUX PUMP 3B",
            executive_summary="Critical integrity assessment: measured 3.42 mm vs 4.00 mm OEM limit.",
            findings=[
                FindingRow(
                    component="Pump 3B Casing",
                    observed_defect="Wall thickness 3.42 mm (loss 1.38 mm)",
                    threshold="4.00 mm Limit",
                    risk_level="CRITICAL",
                    citation="[CIT-01] inspection_report.pdf"
                )
            ],
            recommendations=["Immediate isolation and casing replacement."],
            signoff_author="Lead Reliability Engineer",
            signoff_role="Asset Integrity"
        )

        docx_res = await docx_tool.execute(
            workspace_id=ws_id,
            input_data=docx_input
        )
        assert docx_res.status == "CREATED"
        artifact_file = artifacts_dir / "Engineering_Approval_Note_Pump3B.docx"
        assert artifact_file.exists()
        assert artifact_file.stat().st_size > 0

        # 8. Cryptographic audit chain verification
        AuditLogger.record_event(
            session=db_session,
            event_type="FLAGSHIP_DEMO_TEST_COMPLETE",
            payload={"workspace_id": ws_id, "status": "PASSED"},
            workspace_id=ws_id
        )
        verify_res = AuditLogger.verify_chain(db_session)
        assert verify_res.is_valid is True
        assert verify_res.verified_count >= 1
    finally:
        settings.WORKSPACES_DIR = orig_workspaces_dir
