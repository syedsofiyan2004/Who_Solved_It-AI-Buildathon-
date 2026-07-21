"""phase 5 keyword search

Revision ID: 202607210003
Revises: 202607200002
Create Date: 2026-07-21
"""

from alembic import op


revision = "202607210003"
down_revision = "202607200002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
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

        CREATE OR REPLACE FUNCTION refresh_challenge_search_from_challenge()
        RETURNS trigger AS $$
        BEGIN
          PERFORM refresh_challenge_search_document(NEW.id);
          RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;

        CREATE OR REPLACE FUNCTION refresh_challenge_search_from_solution()
        RETURNS trigger AS $$
        BEGIN
          PERFORM refresh_challenge_search_document(NEW.challenge_id);
          RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;

        CREATE OR REPLACE FUNCTION refresh_challenge_search_from_technology()
        RETURNS trigger AS $$
        BEGIN
          IF TG_OP = 'DELETE' THEN
            PERFORM refresh_challenge_search_document(OLD.challenge_id);
            RETURN OLD;
          END IF;
          PERFORM refresh_challenge_search_document(NEW.challenge_id);
          RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;

        CREATE TRIGGER challenges_search_document_trigger
        AFTER INSERT OR UPDATE OF title, problem_description, symptoms, exact_error_message, environment, deleted_at ON challenges
        FOR EACH ROW EXECUTE FUNCTION refresh_challenge_search_from_challenge();

        CREATE TRIGGER solutions_search_document_trigger
        AFTER INSERT OR UPDATE OF root_cause, resolution_steps, prevention_notes, deleted_at ON solutions
        FOR EACH ROW EXECUTE FUNCTION refresh_challenge_search_from_solution();

        CREATE TRIGGER challenge_technologies_search_document_trigger
        AFTER INSERT OR UPDATE OF technology_id OR DELETE ON challenge_technologies
        FOR EACH ROW EXECUTE FUNCTION refresh_challenge_search_from_technology();

        SELECT refresh_challenge_search_document(id) FROM challenges;
        """
    )


def downgrade() -> None:
    op.execute(
        """
        DROP TRIGGER IF EXISTS challenge_technologies_search_document_trigger ON challenge_technologies;
        DROP TRIGGER IF EXISTS solutions_search_document_trigger ON solutions;
        DROP TRIGGER IF EXISTS challenges_search_document_trigger ON challenges;
        DROP FUNCTION IF EXISTS refresh_challenge_search_from_technology();
        DROP FUNCTION IF EXISTS refresh_challenge_search_from_solution();
        DROP FUNCTION IF EXISTS refresh_challenge_search_from_challenge();
        DROP FUNCTION IF EXISTS refresh_challenge_search_document(uuid);
        UPDATE challenges SET search_document = NULL;
        """
    )
