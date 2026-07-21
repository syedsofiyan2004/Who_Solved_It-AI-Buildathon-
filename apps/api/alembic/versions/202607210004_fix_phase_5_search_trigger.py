"""fix phase 5 search trigger scoping

Revision ID: 202607210004
Revises: 202607210003
Create Date: 2026-07-21
"""

from alembic import op


revision = "202607210004"
down_revision = "202607210003"
branch_labels = None
depends_on = None


FUNCTION = """
CREATE OR REPLACE FUNCTION refresh_challenge_search_document(p_challenge_id uuid)
RETURNS void AS $$
BEGIN
  WITH source AS (
    SELECT challenge.id, challenge.title, challenge.exact_error_message,
           challenge.symptoms, challenge.problem_description, challenge.environment,
           (SELECT root_cause FROM solutions WHERE solutions.challenge_id = challenge.id AND solutions.deleted_at IS NULL LIMIT 1) AS root_cause,
           (SELECT prevention_notes FROM solutions WHERE solutions.challenge_id = challenge.id AND solutions.deleted_at IS NULL LIMIT 1) AS prevention_notes,
           (SELECT coalesce(string_agg(value, ' '), '') FROM solutions CROSS JOIN LATERAL jsonb_array_elements_text(solutions.resolution_steps) AS value WHERE solutions.challenge_id = challenge.id AND solutions.deleted_at IS NULL) AS steps,
           (SELECT string_agg(technology.name::text, ' ') FROM challenge_technologies JOIN technologies AS technology ON technology.id = challenge_technologies.technology_id WHERE challenge_technologies.challenge_id = challenge.id AND technology.deleted_at IS NULL) AS technology_names
    FROM challenges AS challenge
    WHERE challenge.id = p_challenge_id
  )
  UPDATE challenges AS challenge
  SET search_document =
      setweight(to_tsvector('english', coalesce(source.title, '') || ' ' || coalesce(source.exact_error_message, '')), 'A') ||
      setweight(to_tsvector('english', coalesce(source.symptoms, '') || ' ' || coalesce(source.problem_description, '') || ' ' || coalesce(source.root_cause, '') || ' ' || coalesce(source.technology_names, '')), 'B') ||
      setweight(to_tsvector('english', coalesce(source.environment, '') || ' ' || coalesce(source.steps, '') || ' ' || coalesce(source.prevention_notes, '')), 'C')
  FROM source
  WHERE challenge.id = source.id;
END;
$$ LANGUAGE plpgsql;
"""


def upgrade() -> None:
    op.execute(FUNCTION)
    op.execute("SELECT refresh_challenge_search_document(id) FROM challenges")


def downgrade() -> None:
    op.execute(FUNCTION)
