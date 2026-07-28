"""phase 6 Bedrock embeddings

Revision ID: 202607210005
Revises: 202607210004
Create Date: 2026-07-21
"""

from alembic import op

revision = "202607210005"
down_revision = "202607210004"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        CREATE TABLE solution_embeddings (
          id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
          solution_id uuid NOT NULL REFERENCES solutions(id) ON DELETE CASCADE,
          searchable_text text NOT NULL,
          embedding vector NOT NULL,
          embedding_model varchar(255) NOT NULL,
          content_hash varchar(64) NOT NULL,
          created_at timestamptz NOT NULL DEFAULT now(),
          updated_at timestamptz NOT NULL DEFAULT now(),
          CONSTRAINT uq_solution_embeddings_content UNIQUE (solution_id, embedding_model, content_hash)
        )
        """
    )
    op.create_index("ix_solution_embeddings_solution_model", "solution_embeddings", ["solution_id", "embedding_model"])


def downgrade() -> None:
    op.drop_index("ix_solution_embeddings_solution_model", table_name="solution_embeddings")
    op.drop_table("solution_embeddings")
