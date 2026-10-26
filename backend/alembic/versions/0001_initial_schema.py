"""Initial schema migration: all 6 tables

Revision ID: 0001_initial_schema
Revises:
Create Date: 2026-10-19 19:30:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "0001_initial_schema"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. tenders
    op.create_table(
        "tenders",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("title", sa.Text(), nullable=False),
        sa.Column("reference_number", sa.String(length=120), nullable=False),
        sa.Column("pdf_path", sa.Text(), nullable=False),
        sa.Column("raw_text", sa.Text(), nullable=True),
        sa.Column("page_count", sa.Integer(), nullable=True),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.UniqueConstraint("reference_number", name="uq_tenders_reference_number"),
    )
    op.create_index("ix_tenders_status", "tenders", ["status"])

    # 2. requirements
    op.create_table(
        "requirements",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "tender_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("tenders.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("category", sa.String(length=50), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("requirement_type", sa.String(length=30), nullable=False),
        sa.Column("operator", sa.String(length=20), nullable=True),
        sa.Column("value", postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column("unit", sa.String(length=50), nullable=True),
        sa.Column("deadline", sa.Date(), nullable=True),
        sa.Column("source_page", sa.Integer(), nullable=False),
        sa.Column("source_quote", sa.Text(), nullable=False),
        sa.Column("llm_confidence", sa.Float(), nullable=True),
        sa.Column("is_mandatory", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("sector_key", sa.String(length=100), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.create_index("ix_requirements_tender_id", "requirements", ["tender_id"])
    op.create_index("ix_requirements_type", "requirements", ["requirement_type"])

    # 3. vendor_documents
    op.create_table(
        "vendor_documents",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "tender_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("tenders.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("vendor_name", sa.String(length=255), nullable=False),
        sa.Column("doc_type", sa.String(length=100), nullable=True),
        sa.Column("original_filename", sa.Text(), nullable=False),
        sa.Column("pdf_path", sa.Text(), nullable=False),
        sa.Column("raw_text", sa.Text(), nullable=True),
        sa.Column("page_count", sa.Integer(), nullable=True),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.create_index("ix_vendor_documents_tender_id", "vendor_documents", ["tender_id"])
    op.create_index("ix_vendor_documents_vendor_name", "vendor_documents", ["vendor_name"])

    # 4. matches
    op.create_table(
        "matches",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "requirement_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("requirements.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "vendor_document_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("vendor_documents.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("verdict", sa.String(length=10), nullable=False),
        sa.Column("verdict_reason", sa.Text(), nullable=False),
        sa.Column("evidence_file", sa.Text(), nullable=True),
        sa.Column("evidence_page", sa.Integer(), nullable=True),
        sa.Column("evidence_quote", sa.Text(), nullable=True),
        sa.Column("extracted_value", postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column("searched_in", postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column("checked_by", sa.String(length=20), nullable=False),
        sa.Column("llm_confidence", sa.Float(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.create_index("ix_matches_requirement_id", "matches", ["requirement_id"])
    op.create_index("ix_matches_verdict", "matches", ["verdict"])

    # 5. reports
    op.create_table(
        "reports",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "tender_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("tenders.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("vendor_name", sa.String(length=255), nullable=False),
        sa.Column("overall_verdict", sa.String(length=20), nullable=False),
        sa.Column("pass_count", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("fail_count", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("missing_count", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("mismatch_count", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("contradiction_count", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("officer_confirmed", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("officer_notes", sa.Text(), nullable=True),
        sa.Column("officer_id", sa.String(length=255), nullable=True),
        sa.Column("confirmed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.create_index("ix_reports_tender_id", "reports", ["tender_id"])
    op.create_index("ix_reports_vendor_name", "reports", ["vendor_name"])

    # 6. contradictions
    op.create_table(
        "contradictions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "tender_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("tenders.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("vendor_name", sa.String(length=255), nullable=False),
        sa.Column("field", sa.String(length=100), nullable=False),
        sa.Column("doc_a_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("doc_a_filename", sa.Text(), nullable=False),
        sa.Column("doc_a_value", sa.Text(), nullable=False),
        sa.Column("doc_b_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("doc_b_filename", sa.Text(), nullable=False),
        sa.Column("doc_b_value", sa.Text(), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.create_index("ix_contradictions_tender_id", "contradictions", ["tender_id"])


def downgrade() -> None:
    op.drop_table("contradictions")
    op.drop_table("reports")
    op.drop_table("matches")
    op.drop_table("vendor_documents")
    op.drop_table("requirements")
    op.drop_table("tenders")
