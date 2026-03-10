"""initial schema

Revision ID: 0001_initial
Revises: 
Create Date: 2026-01-31 12:00:00
"""

from alembic import op
import sqlalchemy as sa


revision = "0001_initial"

down_revision = None

branch_labels = None

depends_on = None


def upgrade() -> None:
    op.create_table(
        "sources",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(), nullable=False, unique=True),
        sa.Column("query", sa.String(), nullable=False),
        sa.Column("region_code", sa.String(), nullable=True),
        sa.Column("relevance_language", sa.String(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
    )
    op.create_table(
        "videos",
        sa.Column("video_id", sa.String(), primary_key=True),
        sa.Column("channel_id", sa.String(), nullable=False),
        sa.Column("title", sa.String(), nullable=False),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("url", sa.String(), nullable=False),
        sa.Column("thumbnail_url", sa.String(), nullable=True),
        sa.Column("category_id", sa.String(), nullable=True),
        sa.Column("first_seen_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("last_checked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("source_name", sa.String(), nullable=True),
    )
    op.create_table(
        "channels",
        sa.Column("channel_id", sa.String(), primary_key=True),
        sa.Column("title", sa.String(), nullable=False),
        sa.Column("subscriber_count", sa.Integer(), nullable=True),
        sa.Column("last_checked_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_table(
        "video_snapshots",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("video_id", sa.String(), sa.ForeignKey("videos.video_id"), nullable=False),
        sa.Column("taken_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("views", sa.Integer(), nullable=False),
        sa.Column("likes", sa.Integer(), nullable=False),
        sa.Column("comments", sa.Integer(), nullable=False),
        sa.Column("subscriber_count_at_time", sa.Integer(), nullable=False),
        sa.Column("raw_json_s3_key", sa.String(), nullable=True),
    )
    op.create_table(
        "alerts_sent",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("sent_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("chat_id", sa.String(), nullable=False),
        sa.Column("payload_hash", sa.String(), nullable=False, unique=True),
    )


def downgrade() -> None:
    op.drop_table("alerts_sent")
    op.drop_table("video_snapshots")
    op.drop_table("channels")
    op.drop_table("videos")
    op.drop_table("sources")
