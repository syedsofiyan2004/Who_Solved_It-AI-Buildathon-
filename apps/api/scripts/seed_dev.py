"""Idempotent fictional-only development corpus. Never use this data for real employee workflows."""

import sys
from datetime import date, timedelta
from pathlib import Path
from uuid import NAMESPACE_URL, uuid5

sys.path.append(str(Path(__file__).resolve().parents[1]))

from app.core.security import hash_password
from app.database.session import SessionLocal
from app.models.auth import AppRole, User
from app.models.repository import (
    Challenge,
    ChallengeTechnology,
    ContentStatus,
    Department,
    EmployeeProfile,
    ReviewDecision,
    Solution,
    Team,
    Technology,
    VerificationReview,
    VisibilityLevel,
)


def stable_id(name: str):
    return uuid5(NAMESPACE_URL, f"technical-knowledge-platform/fictional/{name}")


DEPARTMENTS = (("Platform Engineering", "platform"), ("Developer Experience", "devex"), ("Security Engineering", "security"))
TEAMS = (("Runtime", "platform"), ("Cloud Foundations", "platform"), ("Build Systems", "devex"), ("Web Platform", "devex"), ("Identity", "security"), ("Application Security", "security"))
TECHNOLOGIES = (
    ("AWS", "cloud"), ("Terraform", "infrastructure"), ("Docker", "containers"), ("Kubernetes", "containers"),
    ("Python", "language"), ("React", "language"), ("PostgreSQL", "database"), ("Linux", "platform"),
    ("Nginx", "networking"), ("GitHub Actions", "ci-cd"), ("OIDC", "security"), ("Redis", "database"),
)
SCENARIOS = (
    ("Docker container cannot import the service package", "ModuleNotFoundError: No module named 'service'", "Docker Compose, Python 3.12", "The image copied the package to an unexpected path.", "Docker", "Correct the Docker COPY path and rebuild the image."),
    ("Terraform state lock blocks a production plan", "Error acquiring the state lock", "Terraform, S3 backend", "A previous interrupted apply retained the lock.", "Terraform", "Verify the active run, release the stale lock, and rerun the plan."),
    ("PostgreSQL migration cannot connect during deployment", "connection to server at 'postgres' failed", "Docker Compose, PostgreSQL 16", "The migration service used the host port instead of the Compose service hostname.", "PostgreSQL", "Use the internal service hostname and rerun the migration."),
    ("React build fails because an environment value is missing", "VITE_API_URL is not defined", "Vite, React 18", "The deployment environment omitted the required build-time value.", "React", "Add the approved public API URL to the build environment and rebuild."),
    ("Kubernetes pod remains in CrashLoopBackOff", "Back-off restarting failed container", "Kubernetes, Linux", "The liveness probe started before the service was ready.", "Kubernetes", "Increase the initial delay and verify the readiness endpoint."),
    ("Nginx returns 502 after an application restart", "connect() failed (111: Connection refused)", "Nginx, Linux", "The upstream port changed without updating the proxy configuration.", "Nginx", "Align the upstream port and reload Nginx after a configuration test."),
    ("GitHub Actions cannot assume the deployment role", "Not authorized to perform sts:AssumeRoleWithWebIdentity", "GitHub Actions, AWS", "The OIDC subject condition did not include the deployment branch.", "OIDC", "Restrict and update the OIDC trust condition for the approved branch."),
    ("Python worker exhausts database connections", "remaining connection slots are reserved", "Python, PostgreSQL", "Connections were created per task and never returned to the pool.", "Python", "Use a bounded shared connection pool and close sessions on completion."),
    ("AWS workload cannot read a configuration parameter", "AccessDeniedException: User is not authorized", "AWS, IAM", "The workload role lacked the narrowly scoped parameter permission.", "AWS", "Add the exact parameter ARN to the role policy and retest with least privilege."),
    ("Redis cache clients time out under load", "Timeout connecting to Redis", "Redis, Linux", "The client pool was smaller than concurrent request demand.", "Redis", "Set a bounded pool size and expose pool saturation metrics."),
    ("Terraform plan proposes unexpected replacements", "forces replacement", "Terraform, AWS", "A resource identity attribute changed after a module upgrade.", "Terraform", "Pin the compatible module version and add an explicit migration plan."),
    ("Frontend callback rejects a valid signed-in user", "invalid_state parameter", "React, OIDC", "Multiple browser tabs overwrote the temporary sign-in state.", "OIDC", "Store per-request state and reject only unmatched callbacks."),
)


def main() -> None:
    with SessionLocal() as db:
        for name, slug in DEPARTMENTS:
            identifier = stable_id(f"department/{slug}")
            if db.get(Department, identifier) is None:
                db.add(Department(id=identifier, name=name, slug=slug))
        db.flush()
        department_by_slug = {slug: stable_id(f"department/{slug}") for _, slug in DEPARTMENTS}
        for name, department_slug in TEAMS:
            slug = name.lower().replace(" ", "-")
            identifier = stable_id(f"team/{slug}")
            if db.get(Team, identifier) is None:
                db.add(Team(id=identifier, department_id=department_by_slug[department_slug], name=name, slug=slug))
        for name, category in TECHNOLOGIES:
            slug = name.lower().replace(" ", "-")
            identifier = stable_id(f"technology/{slug}")
            if db.get(Technology, identifier) is None:
                db.add(Technology(id=identifier, name=name, slug=slug, category=category))
        db.flush()

        password_hash = hash_password("development-only-password")
        users: list[User] = []
        for index in range(24):
            team_name, department_slug = TEAMS[index % len(TEAMS)]
            team_slug = team_name.lower().replace(" ", "-")
            identifier = stable_id(f"user/{index}")
            role = AppRole.ADMINISTRATOR if index == 0 else AppRole.REVIEWER if index in {1, 2, 3} else AppRole.EMPLOYEE
            email = f"fictional.engineer.{index + 1}@example.test"
            user = db.get(User, identifier)
            if user is None:
                user = User(id=identifier, email=email, password_hash=password_hash, role=role, is_active=True)
                db.add(user)
            users.append(user)
            if db.get(EmployeeProfile, identifier) is None:
                db.add(EmployeeProfile(user_id=identifier, display_name=f"Fictional Engineer {index + 1}", job_title="Software Engineer", department_id=department_by_slug[department_slug], team_id=stable_id(f"team/{team_slug}"), contact_email=email, bio="Fictional development profile."))
        db.flush()

        technology_by_name = {name: stable_id(f"technology/{name.lower().replace(' ', '-')}") for name, _ in TECHNOLOGIES}
        for index in range(36):
            title, error, environment, root_cause, technology, resolution = SCENARIOS[index % len(SCENARIOS)]
            owner = users[index % len(users)]
            team_name, department_slug = TEAMS[index % len(TEAMS)]
            team_slug = team_name.lower().replace(" ", "-")
            challenge_id = stable_id(f"challenge/{index}")
            solution_id = stable_id(f"solution/{index}")
            status = ContentStatus.VERIFIED if index < 30 else ContentStatus.SUBMITTED if index < 33 else ContentStatus.DRAFT
            visibility = VisibilityLevel.COMPANY if index % 5 else VisibilityLevel.DEPARTMENT if index % 3 else VisibilityLevel.TEAM
            if db.get(Challenge, challenge_id) is None:
                db.add(Challenge(id=challenge_id, title=f"{title} ({index + 1})", problem_description=f"Fictional incident: {title.lower()} during a controlled development deployment.", symptoms=f"Fictional symptom recorded for {technology} troubleshooting.", exact_error_message=error, environment=environment, status=status, visibility=visibility, department_id=department_by_slug[department_slug], team_id=stable_id(f"team/{team_slug}"), owner_user_id=owner.id, created_by_user_id=owner.id, updated_by_user_id=owner.id))
                db.add(Solution(id=solution_id, challenge_id=challenge_id, root_cause=root_cause, resolution_steps=[resolution, "Confirm the result with an approved verification step."], code_snippets=[], prevention_notes="Document the validated configuration change.", status=status, solved_at=date.today() - timedelta(days=index + 1), primary_owner_user_id=owner.id))
                db.add(ChallengeTechnology(challenge_id=challenge_id, technology_id=technology_by_name[technology]))
                if status == ContentStatus.VERIFIED:
                    reviewer = users[1 if owner.id != users[1].id else 2]
                    db.add(VerificationReview(id=stable_id(f"review/{index}"), solution_id=solution_id, reviewer_user_id=reviewer.id, decision=ReviewDecision.VERIFIED, notes="Fictional development review.", visibility_after=visibility))
        db.commit()
        counts = {status.value: db.query(Challenge).filter(Challenge.status == status).count() for status in ContentStatus}
    print(f"Fictional development corpus is ready: 24 employees, 36 solutions; statuses={counts}.")


if __name__ == "__main__":
    main()
