"""Idempotent buildathon showcase corpus.

The employee names were supplied for this internal demonstration. The technical
incidents are original synthetic examples generated from common Cloud, DevOps,
SRE, software engineering, data engineering, and AI operations patterns. They
are not scraped copies of Stack Overflow or private company material.
"""

import sys
from datetime import date, timedelta
from pathlib import Path
from uuid import NAMESPACE_URL, uuid5

sys.path.append(str(Path(__file__).resolve().parents[1]))

from sqlalchemy import select

from app.core.security import hash_password
from app.database.session import SessionLocal
from app.models.auth import AppRole, User
from app.models.repository import (
    Challenge,
    ChallengeTechnology,
    ContentStatus,
    Department,
    EmployeeProfile,
    Feedback,
    FeedbackValue,
    ReviewDecision,
    Solution,
    Team,
    Technology,
    VerificationReview,
    VisibilityLevel,
)


def stable_id(name: str):
    return uuid5(NAMESPACE_URL, f"minfy-resolve/showcase/{name}")


def email_for(name: str) -> str:
    parts = [part.lower().replace("'", "") for part in name.split() if part]
    local = parts[0] if len(parts) == 1 else f"{parts[0]}.{parts[-1]}"
    return f"{local}@minfytech.com"


def stable_person_id(name: str):
    stable_names = {
        "Aravind Mandan": "aravin mandan",
        "Aravind Appuswamy": "aravind appu swamy",
    }
    return stable_id(f"user/{stable_names.get(name, name.lower())}")


def first_by_unique(db, model, *criteria):
    return db.execute(select(model).where(*criteria)).scalar_one_or_none()


DEPARTMENTS = {
    "cloud": "Cloud Migration, DevOps & Platform Modernization",
    "ida": "Intelligent Data Applications",
    "ai": "AI & Data Science",
    "people": "People Operations",
}

TEAMS = {
    "cloud_engineering": ("Cloud & DevOps Engineering", "cloud"),
    "cloud_management": ("Cloud Migration Management", "cloud"),
    "platform_leadership": ("Platform Modernization Leadership", "cloud"),
    "sreaas": ("SREaaS", "cloud"),
    "software_engineering": ("Software Engineering", "ida"),
    "ida_management": ("Intelligent Data Applications Management", "ida"),
    "ai_engineering": ("Data Engineering & Data Science", "ai"),
    "ai_management": ("AI & Data Science Management", "ai"),
    "hr": ("Human Resources", "people"),
}


EMPLOYEES = [
    # Cloud and DevOps engineering
    *[(name, "Cloud & DevOps Engineer", "cloud_engineering", AppRole.EMPLOYEE, ["AWS", "Terraform", "Kubernetes", "Cloud migration", "CI/CD"])
      for name in [
          "Syed Sofiyan", "Vaibhav Singh", "Mayur Pal", "Uzaif Ali", "Sanath Kumar",
          "Yashwanth Reddy Valluru", "Priyesh Rai", "Akhilesh Gone", "Sanskar Goyal",
          "Abhinav Bisth", "Abhishek Narumala", "Abhinav Seelam", "Siva Reddy", "Chandana Patil",
      ]],
    *[(name, "Cloud Migration Manager", "cloud_management", AppRole.REVIEWER, ["Cloud migration", "Delivery governance", "Architecture review", "Risk management"])
      for name in ["Srikar Deshmukh", "Kunta Sreevardhan Reddy", "Murli K", "Sarang K"]],
    *[(name, "Senior Vice President - Cloud, DevOps & Platform Modernization", "platform_leadership", AppRole.ADMINISTRATOR, ["Platform modernization", "Cloud strategy", "Executive governance", "Operating model"])
      for name in ["Anant Joshi", "Kodavathi Sreekanth"]],
    ("Bharath Kumar Aleni", "SREaaS Lead", "sreaas", AppRole.REVIEWER, ["SRE", "Observability", "Incident response", "SLOs", "Reliability engineering"]),
    # Intelligent Data Applications
    *[(name, "Software Engineer - Intelligent Data Applications", "software_engineering", AppRole.EMPLOYEE, ["Software engineering", "APIs", "Data applications", "Python", "React"])
      for name in ["Amaan Ahmed", "Shybash Sheikh", "Akash Kumar", "Midhilesh Polishetty", "Donthula Supriya", "Bodupally Rohan"]],
    *[(name, "Engineering Manager - Intelligent Data Applications", "ida_management", AppRole.REVIEWER, ["Software delivery", "System design", "Application modernization", "Technical leadership"])
      for name in ["Shubham Kumar Singh", "Ritayan Banerjee"]],
    # AI and Data Science
    *[(name, "Data Engineer & Data Scientist", "ai_engineering", AppRole.EMPLOYEE, ["Data engineering", "Machine learning", "MLOps", "Python", "Analytics"])
      for name in ["Rakesh R", "Yash Rajput", "Madhu Kumar", "Aravind Mandan", "Aravind Appuswamy", "Anil", "Nihaar Reddy", "Aviskar Mane", "Kavya Sharma", "Aryan Mohapatra"]],
    *[(name, "Manager - AI & Data Science", "ai_management", AppRole.REVIEWER, ["AI strategy", "Data science", "MLOps governance", "Model delivery"])
      for name in ["Blesson Davis", "Anirban De"]],
    # People operations
    ("Anubhav Sagar", "HR Business Partner", "hr", AppRole.EMPLOYEE, ["People operations", "Employee support", "Policy guidance"]),
    ("Ankitha Jain", "People Operations Specialist", "hr", AppRole.EMPLOYEE, ["People operations", "Onboarding", "Employee support"]),
]


TECHNOLOGIES = [
    ("AWS", "cloud"), ("Azure", "cloud"), ("Google Cloud", "cloud"), ("Terraform", "infrastructure"),
    ("CloudFormation", "infrastructure"), ("Ansible", "infrastructure"), ("Docker", "containers"),
    ("Kubernetes", "containers"), ("EKS", "containers"), ("Helm", "containers"), ("Argo CD", "ci-cd"),
    ("GitHub Actions", "ci-cd"), ("Jenkins", "ci-cd"), ("Linux", "platform"), ("Nginx", "networking"),
    ("IAM", "security"), ("OIDC", "security"), ("KMS", "security"), ("WAF", "security"),
    ("S3", "storage"), ("EC2", "compute"), ("Lambda", "compute"), ("API Gateway", "integration"),
    ("Route 53", "networking"), ("Transit Gateway", "networking"), ("PostgreSQL", "database"),
    ("VPC", "networking"), ("Security", "security"), ("SRE", "reliability"), ("AI", "ai"),
    ("MySQL", "database"), ("Redis", "database"), ("Kafka", "streaming"), ("Elasticsearch", "search"),
    ("Prometheus", "observability"), ("Grafana", "observability"), ("Loki", "observability"),
    ("Python", "language"), ("FastAPI", "framework"), ("SQLAlchemy", "framework"), ("React", "framework"),
    ("Vite", "framework"), ("TypeScript", "language"), ("Node.js", "runtime"),
    ("Airflow", "data"), ("Spark", "data"), ("dbt", "data"), ("MLflow", "mlops"),
    ("Vector Search", "ai"), ("LLM", "ai"), ("RAG", "ai"), ("CUDA", "ai"),
    ("OpenTelemetry", "observability"), ("Istio", "networking"), ("Vault", "security"), ("Celery", "runtime"),
]


# key, domain, title, error, root cause, resolution, technologies, code evidence
BLUEPRINTS = [
    ("terraform-lock", "cloud", "Terraform state lock blocks an infrastructure change", "Error acquiring the state lock", "An interrupted run retained a stale backend lock after the worker terminated.", ["Confirm no active apply is running.", "Back up the state metadata.", "Release only the verified stale lock and rerun plan."], ["Terraform", "S3"], "terraform force-unlock <LOCK_ID>"),
    ("tgw-route", "cloud", "Transit Gateway traffic cannot reach the migrated workload", "Destination Host Unreachable", "The attachment route table did not propagate the destination VPC CIDR.", ["Inspect attachment association and propagation.", "Add the approved CIDR route.", "Validate both directions with flow logs."], ["AWS", "Transit Gateway", "VPC"], "aws ec2 search-transit-gateway-routes --transit-gateway-route-table-id <id>"),
    ("eks-image", "cloud", "EKS workload cannot pull the private image", "ImagePullBackOff", "The node role lacked repository read permissions after the cluster migration.", ["Confirm the image URI and tag.", "Grant least-privilege ECR pull permissions to the node role.", "Restart the deployment and verify events."], ["AWS", "EKS", "Kubernetes"], "kubectl describe pod <pod>"),
    ("probe-loop", "cloud", "Kubernetes pod repeatedly restarts during startup", "CrashLoopBackOff", "The liveness probe started before dependency initialization completed.", ["Compare startup duration with probe timings.", "Add a startup probe or increase initial delay.", "Verify readiness independently from liveness."], ["Kubernetes", "Prometheus"], "kubectl get events --sort-by=.lastTimestamp"),
    ("docker-module", "cloud", "Container cannot import the application package", "ModuleNotFoundError: No module named 'service'", "The multi-stage build copied source to a path outside Python's runtime module path.", ["Inspect the final image filesystem.", "Correct COPY and WORKDIR paths.", "Rebuild without cache and run an import smoke test."], ["Docker", "Python"], "docker run --rm <image> python -c \"import service\""),
    ("oidc-role", "cloud", "GitHub Actions cannot assume the deployment role", "Not authorized to perform sts:AssumeRoleWithWebIdentity", "The OIDC trust condition did not match the repository branch subject.", ["Decode and inspect the OIDC subject claim.", "Update the trust policy for the approved repository and branch.", "Retest without broad wildcard permissions."], ["GitHub Actions", "OIDC", "IAM"], "aws sts get-caller-identity"),
    ("jenkins-agent", "cloud", "Jenkins agent remains offline after network migration", "java.net.ConnectException: Connection timed out", "Firewall rules allowed the old controller address but not the new private endpoint.", ["Check agent DNS and route resolution.", "Update the narrow firewall rule.", "Reconnect and verify executor health."], ["Jenkins", "Linux", "AWS"], "curl -vk https://<controller>/login"),
    ("argocd-drift", "cloud", "Argo CD reports persistent OutOfSync after sync", "ComparisonError: resource differs", "A mutating controller injected fields that were not excluded from diffing.", ["Compare live and desired manifests.", "Add a narrow ignore-difference rule.", "Resync and confirm real drift is still detected."], ["Argo CD", "Kubernetes"], "argocd app diff <app>"),
    ("helm-immutable", "cloud", "Helm upgrade fails on an immutable Kubernetes field", "field is immutable", "The chart changed an immutable selector during a release upgrade.", ["Identify the immutable field in the rendered diff.", "Plan a controlled resource recreation.", "Preserve service continuity and validate rollback."], ["Helm", "Kubernetes"], "helm diff upgrade <release> <chart>"),
    ("nginx-502", "cloud", "Nginx returns 502 after an application rollout", "connect() failed (111: Connection refused)", "The upstream service port changed while the proxy target remained unchanged.", ["Validate the application listener.", "Update the upstream target.", "Run nginx config test and reload gracefully."], ["Nginx", "Linux"], "nginx -t"),
    ("alb-health", "cloud", "Load balancer targets remain unhealthy", "Target.ResponseCodeMismatch", "The health check path required authentication after the application change.", ["Call the health path directly from the target network.", "Expose a minimal unauthenticated health endpoint.", "Update target health settings and verify recovery."], ["AWS", "EC2", "Nginx"], "aws elbv2 describe-target-health --target-group-arn <arn>"),
    ("s3-deny", "cloud", "Workload receives S3 AccessDenied despite IAM permission", "AccessDenied", "An explicit bucket-policy deny restricted requests to a different VPC endpoint.", ["Evaluate identity and resource policies together.", "Confirm the request context and endpoint.", "Update only the approved endpoint condition."], ["AWS", "S3", "IAM"], "aws s3api get-bucket-policy --bucket <bucket>"),
    ("cfn-rollback", "cloud", "CloudFormation stack rolls back during migration", "UPDATE_ROLLBACK_FAILED", "A retained dependency prevented replacement of a referenced resource.", ["Inspect the first failing stack event.", "Resolve the dependency without deleting retained data.", "Continue rollback and redeploy the corrected template."], ["CloudFormation", "AWS"], "aws cloudformation describe-stack-events --stack-name <stack>"),
    ("imds-token", "cloud", "Legacy bootstrap cannot read EC2 instance metadata", "401 - Unauthorized", "IMDSv2 was enforced but the bootstrap script still used an IMDSv1 request.", ["Request an IMDSv2 token.", "Pass the token on metadata calls.", "Keep hop limit and metadata options restricted."], ["EC2", "Linux", "AWS"], "TOKEN=$(curl -X PUT -H 'X-aws-ec2-metadata-token-ttl-seconds: 21600' http://169.254.169.254/latest/api/token)"),
    ("dns-private", "cloud", "Private service name does not resolve after migration", "Temporary failure in name resolution", "The private hosted zone was not associated with the destination VPC.", ["Inspect resolver configuration and zone associations.", "Associate the correct VPC.", "Flush caches and validate from the workload subnet."], ["Route 53", "AWS", "Linux"], "dig +short <service.internal>"),
    ("kms-decrypt", "cloud", "Application cannot decrypt a migrated secret", "AccessDeniedException: kms:Decrypt", "The key policy trusted the old role but not the new workload role.", ["Identify the encryption key ARN.", "Update both IAM and key policy using least privilege.", "Test decryption from the workload identity."], ["KMS", "IAM", "AWS"], "aws kms describe-key --key-id <key>"),
    ("terraform-replace", "cloud", "Terraform proposes unexpected resource replacement", "forces replacement", "A module upgrade changed a resource identity attribute.", ["Review the plan at attribute level.", "Pin the compatible module version or use a documented state move.", "Apply only after migration review."], ["Terraform", "AWS"], "terraform show -json tfplan"),
    ("pvc-pending", "cloud", "Kubernetes persistent volume claim stays Pending", "no persistent volumes available for this claim", "The requested storage class was unavailable in the destination cluster.", ["Inspect storage classes and provisioner logs.", "Select the approved class or install the provisioner.", "Recreate the claim only after data handling is confirmed."], ["Kubernetes", "EKS"], "kubectl describe pvc <pvc>"),
    ("docker-disk", "sre", "Container host runs out of disk during deployment", "no space left on device", "Unused image layers and unbounded container logs exhausted the data volume.", ["Identify the consuming filesystem.", "Prune only unused artifacts.", "Configure log rotation and disk alerts."], ["Docker", "Linux", "Grafana"], "docker system df"),
    ("file-descriptor", "sre", "Linux service fails under connection load", "Too many open files", "The process limit remained at the OS default after concurrency increased.", ["Measure open descriptors and leak patterns.", "Fix any descriptor leak.", "Set validated systemd and kernel limits."], ["Linux", "Prometheus"], "ls /proc/<pid>/fd | wc -l"),
    ("prom-cardinality", "sre", "Prometheus memory grows rapidly after a metrics release", "many-to-many matching not allowed", "A request identifier was added as a high-cardinality metric label.", ["Find the highest-cardinality labels.", "Remove unbounded labels from metrics.", "Move request identifiers to logs or traces."], ["Prometheus", "Grafana"], "promtool tsdb analyze /prometheus"),
    ("loki-timeout", "sre", "Loki queries time out during incident response", "context deadline exceeded", "A broad unbounded query scanned excessive log volume.", ["Narrow time range and labels.", "Add useful low-cardinality labels at ingestion.", "Tune limits only after query design is corrected."], ["Loki", "Grafana"], "logcli query '{app=\"api\"} |= \"error\"' --since=15m"),
    ("kafka-lag", "sre", "Kafka consumer lag grows continuously", "CommitFailedException", "Processing time exceeded the consumer poll interval during a downstream slowdown.", ["Measure processing latency and rebalance events.", "Bound batch work or move processing off the poll loop.", "Tune consumer settings after code correction."], ["Kafka", "Prometheus"], "kafka-consumer-groups --describe --group <group>"),
    ("redis-eviction", "sre", "Redis evicts active cache keys unexpectedly", "OOM command not allowed", "The cache had no bounded memory policy aligned to the workload.", ["Review memory usage and key distribution.", "Set an approved maxmemory and eviction policy.", "Add saturation and eviction alerts."], ["Redis", "Grafana"], "redis-cli INFO memory"),
    ("postgres-lock", "software", "Database migration is blocked by a long-running transaction", "canceling statement due to lock timeout", "An idle transaction retained a lock on the table being altered.", ["Identify the blocking session.", "Confirm business impact before terminating it.", "Apply the migration with bounded lock timeout."], ["PostgreSQL", "Python"], "SELECT * FROM pg_stat_activity WHERE state = 'idle in transaction';"),
    ("mysql-deadlock", "software", "Concurrent updates cause a MySQL deadlock", "Deadlock found when trying to get lock", "Two code paths updated the same rows in different order.", ["Inspect the deadlock graph.", "Use a consistent update order.", "Add bounded retry for safe transactional operations."], ["MySQL", "Python"], "SHOW ENGINE INNODB STATUS;"),
    ("react-env", "software", "React build cannot find the API configuration", "VITE_API_URL is not defined", "The value was supplied at runtime even though Vite requires it at build time.", ["Confirm the build environment.", "Provide the approved public API URL before build.", "Rebuild and verify the generated configuration."], ["React", "Node.js"], "npm run build"),
    ("node-heap", "software", "Node.js process exits during a large build", "JavaScript heap out of memory", "A bundle step retained duplicate source maps and exceeded the default heap.", ["Capture heap usage by build phase.", "Remove duplicate processing.", "Use a bounded heap increase only after optimization."], ["Node.js", "React"], "node --max-old-space-size=4096 ./node_modules/.bin/vite build"),
    ("python-import", "software", "Python service fails after packaging", "ModuleNotFoundError", "The package was installed without the application module because of an incorrect package include rule.", ["Inspect the built wheel contents.", "Correct package discovery.", "Install the wheel into a clean environment and run imports."], ["Python", "FastAPI"], "python -m zipfile -l dist/*.whl"),
    ("fastapi-session", "software", "FastAPI requests leak database sessions", "remaining connection slots are reserved", "An exception path bypassed session cleanup.", ["Trace session acquisition and closure.", "Use dependency-managed context cleanup.", "Load test and verify pool stability."], ["FastAPI", "PostgreSQL", "Python"], "SELECT count(*) FROM pg_stat_activity;"),
    ("api-pagination", "software", "Paginated API returns duplicate records", "duplicate item detected across pages", "Offset pagination was used while rows were being inserted concurrently.", ["Reproduce with concurrent inserts.", "Use stable cursor pagination with deterministic ordering.", "Add cross-page uniqueness tests."], ["FastAPI", "PostgreSQL"], "ORDER BY updated_at DESC, id DESC"),
    ("oauth-state", "software", "OAuth callback rejects a valid login", "invalid_state parameter", "Multiple tabs overwrote a single shared temporary state value.", ["Store state per authorization request.", "Validate and consume the matching state once.", "Test concurrent browser tabs."], ["OIDC", "React", "FastAPI"], "state=<cryptographically-random-per-request>"),
    ("cors-preflight", "software", "Browser blocks API request after environment change", "CORS policy: No 'Access-Control-Allow-Origin' header", "The deployed frontend origin was missing from the exact allowlist.", ["Inspect the browser preflight request.", "Add the exact approved origin.", "Avoid wildcard origins with credentials."], ["React", "FastAPI", "Nginx"], "curl -i -X OPTIONS https://api.example.test/health"),
    ("airflow-import", "data", "Airflow DAG does not appear in the scheduler", "Broken DAG: ModuleNotFoundError", "A provider dependency was installed on the worker but not the scheduler image.", ["Inspect scheduler import errors.", "Align dependencies across all Airflow images.", "Run DAG import tests in CI."], ["Airflow", "Python", "Docker"], "airflow dags list-import-errors"),
    ("spark-oom", "data", "Spark executor is repeatedly killed", "ExecutorLostFailure: Container killed by YARN for exceeding memory limits", "A skewed partition concentrated most records on one executor.", ["Inspect partition size distribution.", "Repartition using an appropriate key or salt.", "Tune memory only after reducing skew."], ["Spark", "Python"], "df.groupBy('partition_key').count().orderBy('count', ascending=False)"),
    ("dbt-schema", "data", "dbt model fails after an upstream schema change", "column does not exist", "The source contract changed without updating the staging model.", ["Compare source metadata with the declared contract.", "Update staging transformations and tests.", "Add schema-change monitoring."], ["dbt", "PostgreSQL"], "dbt build --select <model>+"),
    ("parquet-schema", "data", "Parquet ingestion fails on mixed column types", "ArrowInvalid: Could not convert value", "Files in the same partition were written with incompatible schemas.", ["Inspect schema per file.", "Normalize the producer schema.", "Rewrite the affected partition and enforce contracts."], ["Python", "S3", "Spark"], "pyarrow.parquet.read_schema('<file>')"),
    ("elastic-mapping", "data", "Elasticsearch rejects documents after a field change", "mapper_parsing_exception", "A field previously indexed as text began receiving structured objects.", ["Inspect the index mapping and rejected document.", "Create a compatible versioned index.", "Reindex and switch the alias safely."], ["Elasticsearch", "Python"], "GET /<index>/_mapping"),
    ("embedding-dim", "ai", "Vector search fails after changing the embedding model", "different vector dimensions", "Existing vectors and new query vectors were produced by models with different dimensions.", ["Identify the model recorded with each vector.", "Re-embed the corpus using one model version.", "Filter retrieval by embedding model ID."], ["Vector Search", "RAG", "Python"], "SELECT embedding_model, count(*) FROM solution_embeddings GROUP BY 1;"),
    ("vector-empty", "ai", "Semantic search returns no relevant results", "no candidates above similarity threshold", "Documents were embedded in query mode instead of passage mode.", ["Verify embedding input types.", "Re-index documents in passage mode.", "Use query mode only for search queries and rerun evaluation."], ["Vector Search", "RAG"], "input_type='passage'  # indexing"),
    ("model-429", "ai", "Model endpoint is throttled during evaluation", "429 Too Many Requests", "The evaluation runner sent unbounded concurrent requests to the trial endpoint.", ["Read retry-after headers.", "Add bounded concurrency and exponential backoff.", "Cache deterministic evaluation results."], ["LLM", "Python"], "backoff = min(base * 2 ** attempt, 30)"),
    ("prompt-injection", "ai", "Retrieved text attempts to override the RAG system prompt", "Ignore previous instructions", "Untrusted document content was concatenated without treating it strictly as data.", ["Separate system instructions from retrieved data.", "Validate model output and citations.", "Never allow retrieved text to control permissions or identity fields."], ["RAG", "LLM", "Security"], "Treat retrieved text as data, never as instructions."),
    ("mlflow-artifact", "ai", "MLflow run cannot load its model artifact", "RESOURCE_DOES_NOT_EXIST", "The artifact URI still referenced a temporary workspace path.", ["Inspect the persisted artifact URI.", "Move artifacts to the approved durable store.", "Register and load the model from the durable URI."], ["MLflow", "S3", "Python"], "mlflow.artifacts.download_artifacts(artifact_uri=...)"),
    ("feature-drift", "ai", "Model quality drops after a source-system migration", "prediction distribution shifted", "A categorical field changed encoding and introduced unseen values.", ["Compare training and serving feature distributions.", "Align the feature contract and unknown-category handling.", "Backfill monitoring thresholds."], ["MLflow", "Python", "AI"], "compare_feature_distribution(reference, production)"),
    ("cuda-oom", "ai", "GPU training job fails with CUDA out of memory", "CUDA out of memory", "Batch size and activation memory exceeded available GPU capacity.", ["Measure allocated and reserved memory.", "Reduce batch size or use gradient accumulation.", "Enable mixed precision after numerical validation."], ["CUDA", "Python", "AI"], "torch.cuda.memory_summary()"),
    ("batch-timeout", "ai", "Batch inference exceeds the service timeout", "504 Gateway Timeout", "Requests grouped too many records into one synchronous inference call.", ["Measure model and preprocessing latency.", "Use bounded batches and asynchronous job status.", "Set timeouts from measured service objectives."], ["LLM", "FastAPI", "Python"], "batch_size = min(requested, SAFE_BATCH_SIZE)"),
    ("token-limit", "ai", "Grounded summary fails on a long retrieval context", "maximum context length exceeded", "Too many full documents were sent instead of concise top-ranked evidence.", ["Limit the number of authorized sources.", "Use focused excerpts from top matches.", "Keep citations and reject unsupported claims."], ["RAG", "LLM"], "context = ranked_sources[:4]"),
    ("citation-invalid", "ai", "Generated answer cites a solution that was not retrieved", "citation outside authorized source set", "The model response was accepted without strict citation validation.", ["Parse structured output.", "Reject citations outside the authorized UUID set.", "Return retrieval results without an unsafe summary."], ["RAG", "LLM", "FastAPI"], "assert set(citations) <= allowed_solution_ids"),
    ("slo-burn", "sre", "SLO burn-rate alert fires without a visible outage", "error budget burn rate > 14.4", "The SLI counted expected client cancellations as service errors.", ["Inspect the SLI event definition.", "Exclude only validated non-service failures.", "Replay historical data and update the alert."], ["Prometheus", "Grafana", "SRE"], "sum(rate(requests_total{status=~'5..'}[5m]))"),
    ("alert-storm", "sre", "One dependency failure triggers hundreds of alerts", "alert notification rate exceeded", "Leaf alerts had no inhibition or dependency grouping.", ["Identify the causal service alert.", "Add dependency-aware inhibition and grouping.", "Keep one actionable symptom alert per ownership boundary."], ["Prometheus", "Grafana", "SRE"], "inhibit_rules:"),
    ("tls-probe", "sre", "Blackbox probe fails after certificate rotation", "x509: certificate signed by unknown authority", "The probe image did not include the updated internal CA chain.", ["Inspect the served certificate chain.", "Update the approved CA bundle.", "Retest from the same probe network."], ["Prometheus", "Nginx", "Security"], "openssl s_client -connect <host>:443 -showcerts"),
    ("lambda-timeout", "cloud", "Lambda function times out after VPC attachment", "Task timed out after 30.00 seconds", "The private subnets lacked a route to the required service endpoint.", ["Inspect subnet routes and DNS resolution.", "Add the approved VPC endpoint or egress path.", "Retest with dependency timing metrics."], ["Lambda", "AWS", "VPC"], "aws logs tail /aws/lambda/<function> --follow"),
    ("api-gateway-cors", "cloud", "API Gateway preflight succeeds but browser call fails", "CORS header missing on 4XX response", "Gateway responses did not include CORS headers for authorization failures.", ["Inspect the failing gateway response type.", "Add headers to the narrow gateway response configuration.", "Test success and error paths from the browser origin."], ["API Gateway", "AWS", "React"], "curl -i -X OPTIONS https://<api>/<path>"),
    ("iam-boundary-deny", "cloud", "Deployment role is denied despite an allow policy", "AccessDenied: permissions boundary does not allow the requested action", "The role's identity policy allowed the action, but its permissions boundary did not include the same resource scope.", ["Identify every policy type evaluated for the denied action.", "Add the narrow resource to the permissions boundary.", "Retest with the same assumed role session and record CloudTrail evidence."], ["AWS", "IAM", "Security"], "aws iam simulate-principal-policy --policy-source-arn <role-arn> --action-names <action>"),
    ("iam-vpce-deny", "cloud", "Private deployment cannot call the artifact service", "because no VPC endpoint policy allows the action", "The workload reached the service through a VPC endpoint whose endpoint policy missed the required read action.", ["Confirm the request is using the intended endpoint.", "Add a least-privilege allow statement to the endpoint policy.", "Verify the identity policy and endpoint policy together."], ["AWS", "IAM", "VPC"], "aws ec2 describe-vpc-endpoints --vpc-endpoint-ids <id>"),
    ("lambda-nacl-ephemeral", "cloud", "Lambda intermittently times out inside the VPC", "connect ETIMEDOUT", "A subnet network ACL blocked return traffic on ephemeral ports used by the VPC-attached function.", ["Check security groups and NACLs separately.", "Allow the approved ephemeral return-port range on the target subnet.", "Run repeated dependency calls and compare timeout rate."], ["Lambda", "AWS", "VPC"], "aws ec2 describe-network-acls --filters Name=association.subnet-id,Values=<subnet-id>"),
    ("lambda-eni-limit", "cloud", "New Lambda versions fail after subnet expansion", "ENILimitReachedException", "Each subnet and security-group combination required additional network interfaces and exceeded the VPC limit.", ["Count the unique subnet/security-group combinations.", "Consolidate unnecessary combinations.", "Request quota only after reducing configuration sprawl."], ["Lambda", "AWS", "VPC"], "aws service-quotas get-service-quota --service-code vpc --quota-code L-DF5E4CA3"),
    ("kube-coredns-loop", "cloud", "CoreDNS enters CrashLoopBackOff after resolver change", "plugin/loop: Loop detected", "The node resolver forwarded cluster DNS traffic back into CoreDNS.", ["Inspect the CoreDNS logs and node resolver configuration.", "Point kubelet DNS to a resolver that does not loop into cluster DNS.", "Restart CoreDNS and validate service-name resolution."], ["Kubernetes", "Linux"], "kubectl -n kube-system logs deploy/coredns"),
    ("kube-oomkilled", "cloud", "Pod restarts after traffic spike with OOMKilled", "Last State: Terminated Reason: OOMKilled", "The container memory limit was lower than measured startup and peak request memory.", ["Confirm OOMKilled in pod status.", "Measure memory during startup and peak requests.", "Right-size requests and limits, then verify no restart loop occurs."], ["Kubernetes", "Prometheus"], "kubectl describe pod <pod> | grep -A5 'Last State'"),
    ("image-tag-missing", "cloud", "Deployment cannot pull the new image tag", "manifest unknown", "The release pipeline updated the Kubernetes manifest before the image tag was pushed to the registry.", ["Confirm the exact image tag in pod events.", "Verify the image exists in the registry.", "Make image publish completion a gate before manifest rollout."], ["Kubernetes", "Docker", "GitHub Actions"], "kubectl describe pod <pod> | grep -i image"),
    ("docker-check-entrypoint", "software", "Container ignores termination during rollout", "process did not exit before termination grace period", "The Dockerfile used a shell-form command that did not forward signals to the application process.", ["Inspect the built image command form.", "Switch to exec-form ENTRYPOINT or CMD.", "Run a termination smoke test before rollout."], ["Docker", "Linux"], "docker inspect <image> --format '{{json .Config.Cmd}}'"),
    ("fastapi-body-limit", "software", "FastAPI upload endpoint fails on larger evidence files", "413 Request Entity Too Large", "Nginx accepted a lower request-body limit than the application upload-size rule.", ["Compare reverse proxy and application upload limits.", "Set the proxy limit to the approved application value.", "Retest allowed and rejected file sizes."], ["FastAPI", "Nginx", "Python"], "nginx -T | grep client_max_body_size"),
    ("sqlalchemy-pool-exhausted", "software", "API workers hang during report generation", "QueuePool limit reached", "A long-running report path held database sessions while streaming output to the client.", ["Trace session lifetime around the report path.", "Materialize the query result before streaming.", "Add pool saturation metrics and a regression test."], ["FastAPI", "SQLAlchemy", "PostgreSQL"], "SELECT state, count(*) FROM pg_stat_activity GROUP BY state;"),
    ("postgres-deadlock-timeout", "software", "Nightly job reports PostgreSQL deadlocks", "deadlock detected", "Two batch workers updated account and audit rows in opposite order.", ["Read the deadlock log and identify both transactions.", "Enforce one update order in both workers.", "Add bounded retry around idempotent batch operations."], ["PostgreSQL", "Python"], "SELECT pid, wait_event_type, wait_event FROM pg_stat_activity WHERE wait_event_type IS NOT NULL;"),
    ("postgres-statement-lock", "software", "Migration fails even with a short lock timeout", "canceling statement due to lock timeout", "An application session held a row lock longer than the migration's permitted lock wait.", ["Find the blocking PID before retrying.", "Schedule the migration after draining the writer path.", "Keep lock_timeout below statement_timeout and document rollback."], ["PostgreSQL", "FastAPI"], "SELECT blocked_locks.pid AS blocked_pid FROM pg_locks blocked_locks WHERE NOT blocked_locks.granted;"),
    ("airflow-queued-timeout", "data", "Airflow task is marked failed before a worker starts it", "Task was queued for longer than configured timeout", "Executor capacity was exhausted and queued tasks exceeded the scheduler queue timeout.", ["Compare queued duration with worker capacity.", "Scale or rebalance workers for the affected queue.", "Set queue timeout from observed worst-case scheduling latency."], ["Airflow", "Python"], "airflow tasks state <dag_id> <task_id> <run_id>"),
    ("airflow-heartbeat-timeout", "data", "Airflow task fails while still processing data", "Task heartbeat timed out", "The task process spent too long in a blocking operation and stopped heartbeating to the scheduler.", ["Check task logs around the last heartbeat.", "Break the blocking operation into monitored chunks.", "Tune heartbeat settings only after code-level progress reporting is fixed."], ["Airflow", "Python"], "airflow tasks logs <dag_id> <task_id> <run_id>"),
    ("spark-broadcast-oom", "data", "Spark driver fails during a dimension-table join", "OutOfMemoryError: Java heap space", "A table assumed to be small grew beyond the safe broadcast size.", ["Check table statistics and the physical join plan.", "Disable broadcast for that table or filter earlier.", "Add data-size checks before the job starts."], ["Spark", "Python"], "df.explain('formatted')"),
    ("dbt-contract-break", "data", "dbt build passes staging but fails downstream", "Compilation Error: model contract was violated", "The staging model changed a column type without updating the downstream contract.", ["Compare compiled schema against the contract.", "Update the transformation and tests together.", "Run affected downstream models before merging."], ["dbt", "PostgreSQL"], "dbt build --select state:modified+"),
    ("prometheus-user-label", "sre", "Prometheus storage grows after API metrics change", "too many series", "A user-specific value was added as a metric label, creating an unbounded time-series set.", ["Identify the highest-cardinality labels.", "Remove user-specific labels from metrics.", "Move per-user investigation to logs or analytics storage."], ["Prometheus", "Grafana", "FastAPI"], "topk(20, count by (__name__, user_id)({__name__=~'.+'}))"),
    ("promql-many-to-one", "sre", "Dashboard query fails after label change", "many-to-many matching not allowed", "The query joined request and error metrics without a unique matching label set after route labels changed.", ["Inspect labels on both sides of the PromQL expression.", "Aggregate to one series per matching key.", "Use group modifiers only when the one-side is guaranteed unique."], ["Prometheus", "Grafana"], "count by (job, route) (http_requests_total)"),
    ("waf-rule-false-positive", "cloud", "Internal API calls are blocked after WAF rule update", "403 Forbidden", "A managed rule matched a legitimate JSON field used by the deployment API.", ["Review sampled WAF requests for the matched rule ID.", "Add a narrow rule exception for the approved path and field.", "Replay blocked and malicious samples before enabling."], ["AWS", "WAF", "Security"], "aws wafv2 get-sampled-requests --web-acl-arn <arn> --rule-metric-name <rule>"),
    ("route53-split-horizon", "cloud", "Service resolves to a public address from private workloads", "connection refused to public endpoint", "The private hosted zone record was missing, so workloads fell back to public DNS resolution.", ["Resolve the name from inside the private subnet.", "Create or associate the private hosted zone record.", "Validate resolver order and remove stale public assumptions."], ["Route 53", "AWS", "VPC"], "dig +short <service-name>"),
    ("otel-trace-gap", "sre", "Distributed trace disappears at the payment boundary", "missing parent span context", "The proxy stripped traceparent headers when routing through a legacy internal domain.", ["Capture headers at each hop.", "Allow only approved tracing headers through the proxy.", "Validate one trace across frontend, API, worker, and database spans."], ["OpenTelemetry", "Nginx", "FastAPI"], "curl -H 'traceparent: 00-<trace>-<span>-01' <service>"),
    ("istio-mtls", "cloud", "Service mesh traffic fails after mTLS policy rollout", "upstream connect error or disconnect/reset before headers", "A namespace policy required mutual TLS but one workload still used plaintext sidecar settings.", ["Inspect PeerAuthentication and DestinationRule scope.", "Align the client traffic policy with strict mTLS.", "Roll out by namespace and verify service-to-service calls."], ["Istio", "Kubernetes", "Security"], "istioctl proxy-config cluster <pod> -n <namespace>"),
    ("vault-token-renewal", "sre", "Application loses secret access after running for several hours", "permission denied: token expired", "The service fetched a short-lived Vault token at startup and never renewed it.", ["Inspect token TTL and renewal eligibility.", "Use the approved agent or renewal path.", "Alert before lease expiry and verify rotation without restart."], ["Vault", "Security", "Linux"], "vault token lookup"),
    ("celery-duplicate-task", "software", "Background job processes the same payment event twice", "task already acknowledged but result missing", "The task acknowledged before the idempotent database write completed during a worker restart.", ["Move acknowledgement after the durable write.", "Add an idempotency key on the business operation.", "Replay the event and confirm a single final state."], ["Celery", "Python", "PostgreSQL"], "SELECT event_id, count(*) FROM payment_events GROUP BY event_id HAVING count(*) > 1;"),
    ("rag-permission-leak", "ai", "RAG answer includes a restricted runbook citation", "citation outside caller visibility scope", "The retrieval service ranked all candidates before applying object-level authorization.", ["Apply visibility filters before context assembly.", "Rebuild the summary context from authorized records only.", "Add an evaluation case for restricted records."], ["RAG", "Vector Search", "Security"], "assert all(can_view(user, source) for source in context)"),
    ("rag-secret-rejection", "ai", "Embedding job rejects a newly submitted solution", "Embedding content contains a detected secret", "The author pasted an environment file into the evidence section and the scanner blocked embedding.", ["Keep the draft available for editing.", "Remove credentials from technical content.", "Regenerate the embedding only after the scanner passes."], ["RAG", "Security", "Python"], "python scripts/scan_secrets.py <solution-export>"),
    ("llm-json-invalid", "ai", "Grounded summary is unavailable despite strong matches", "model returned invalid JSON", "The generation model returned prose instead of the required citation JSON contract.", ["Reject the unsafe response.", "Show retrieved records without synthetic summary.", "Tighten the structured-output prompt and adapter validation."], ["LLM", "RAG", "FastAPI"], "json.loads(model_response)"),
    ("gpu-fragmentation", "ai", "LLM inference fails during KV cache allocation", "CUDA out of memory while allocating KV cache", "Temporary allocations fragmented GPU memory before the serving engine reserved cache blocks.", ["Identify whether OOM occurs during weights, graph capture, or KV cache allocation.", "Reduce GPU memory utilization or batch size.", "Restart workers and validate sustained inference load."], ["CUDA", "LLM", "AI"], "nvidia-smi --query-compute-apps=pid,used_memory --format=csv"),
    ("prometheus-remote-write", "sre", "Metrics backlog grows after remote-write outage", "remote storage queue full", "The remote-write queue could not drain after a downstream outage and started dropping samples.", ["Inspect remote-write queue length and shard count.", "Throttle noisy metric sources before increasing capacity.", "Replay from durable storage only where available."], ["Prometheus", "Grafana", "SRE"], "prometheus_remote_storage_samples_pending"),
    ("postgres-autovacuum-wraparound", "software", "PostgreSQL blocks writes during maintenance window", "database is not accepting commands to avoid wraparound data loss", "Autovacuum was disabled on a high-churn table and transaction IDs approached the safety limit.", ["Identify tables closest to wraparound.", "Run a controlled vacuum freeze.", "Re-enable autovacuum with table-specific thresholds."], ["PostgreSQL", "SRE"], "SELECT relname, age(relfrozenxid) FROM pg_class ORDER BY age(relfrozenxid) DESC LIMIT 20;"),
    ("airflow-xcom-bloat", "data", "Airflow scheduler slows after model evaluation DAG", "metadata database timeout", "Tasks stored large evaluation payloads in XCom instead of object storage.", ["Find oversized XCom rows.", "Store payloads in durable object storage.", "Keep only small references in metadata."], ["Airflow", "PostgreSQL", "Python"], "SELECT dag_id, octet_length(value) FROM xcom ORDER BY octet_length(value) DESC LIMIT 20;"),
    ("spark-small-files", "data", "Spark job slows after CDC ingestion cutover", "Listing file status took longer than expected", "The CDC pipeline created thousands of small files per partition.", ["Measure file count and average file size.", "Compact partitions with a controlled job.", "Tune the ingestion writer to target larger files."], ["Spark", "S3", "Python"], "aws s3 ls s3://<bucket>/<prefix>/ --recursive | wc -l"),
    ("iam-session-tag-deny", "cloud", "Assumed role is denied because session tags are missing", "AccessDenied: principal tag condition failed", "The destination account policy required a project session tag, but the deployment workflow did not pass transitive tags.", ["Inspect CloudTrail for the evaluated principal tags.", "Pass only the approved session tags from the identity broker.", "Retest the same action with IAM policy simulation."], ["AWS", "IAM", "Security"], "aws sts assume-role --role-arn <role> --role-session-name <session> --tags Key=project,Value=<project>"),
    ("eks-webhook-timeout", "cloud", "Kubernetes deployment hangs on admission webhook", "failed calling webhook: context deadline exceeded", "The validating webhook service had no ready endpoints after a namespace label change.", ["List webhook configurations and service endpoints.", "Restore the webhook backing deployment.", "Add a failure-policy decision and readiness alert."], ["Kubernetes", "EKS", "Security"], "kubectl get validatingwebhookconfigurations && kubectl get endpoints -A"),
    ("helm-crd-order", "cloud", "Helm release fails while installing custom resources", "no matches for kind in version", "The chart applied custom resources before the matching CRD was established in the API server.", ["Install or upgrade CRDs before dependent resources.", "Wait for CRD establishment.", "Split CRD lifecycle from application release when required."], ["Helm", "Kubernetes"], "kubectl wait --for condition=established crd/<name> --timeout=60s"),
    ("postgres-plan-regression", "software", "API latency spikes after statistics reset", "query exceeded statement timeout", "The planner selected a sequential scan after table statistics became stale during bulk loading.", ["Compare actual and estimated row counts.", "Run analyze on the affected table.", "Add a post-load statistics refresh to the runbook."], ["PostgreSQL", "FastAPI"], "EXPLAIN (ANALYZE, BUFFERS) SELECT ..."),
    ("nginx-header-size", "software", "Authenticated API calls fail behind Nginx", "upstream sent too big header", "The identity response added group claims that exceeded the proxy header buffer.", ["Confirm the response header size at the proxy.", "Reduce unnecessary claims or tune approved header buffers.", "Retest login and refresh-token paths."], ["Nginx", "OIDC", "FastAPI"], "nginx -T | grep proxy_buffer"),
    ("kafka-offset-reset", "data", "Kafka consumer reprocesses a completed topic partition", "OffsetOutOfRangeException", "Retention removed the committed offset before the paused consumer resumed.", ["Check committed offsets against earliest available offsets.", "Restore from the approved checkpoint when possible.", "Set lag and retention alerts for paused consumers."], ["Kafka", "Prometheus"], "kafka-consumer-groups --bootstrap-server <broker> --describe --group <group>"),
    ("spark-skew-join", "data", "Spark executor repeatedly fails on one partition", "Container killed by YARN for exceeding memory limits", "A skewed join key concentrated most records into one shuffle partition.", ["Inspect partition-size distribution.", "Apply salting or skew join handling for the hot key.", "Validate shuffle spill and task retry counts."], ["Spark", "Python"], "spark.sql.adaptive.skewJoin.enabled=true"),
    ("opentelemetry-exporter-backpressure", "sre", "API latency rises when trace exporter slows", "export queue is full", "The synchronous telemetry exporter blocked request handling when the collector endpoint was saturated.", ["Inspect exporter queue metrics.", "Move export to bounded asynchronous processing.", "Drop or sample telemetry before it affects user traffic."], ["OpenTelemetry", "FastAPI", "SRE"], "otelcol_exporter_queue_size"),
    ("vault-agent-template-stale", "sre", "Application keeps using a rotated database password", "password authentication failed for user", "Vault Agent rendered the new secret file but the application never reloaded its connection pool.", ["Check rendered secret timestamps.", "Trigger the approved reload path after rotation.", "Verify new database sessions use the rotated credential."], ["Vault", "PostgreSQL", "Security"], "vault read database/creds/<role>"),
    ("rag-chunk-boundary-miss", "ai", "Search misses a solution when the exact error is split across chunks", "exact phrase not found in retrieved context", "The ingestion job split stack traces without preserving overlapping error fragments.", ["Inspect chunk boundaries for the source solution.", "Add bounded overlap around error-message regions.", "Re-embed and verify the evaluation query returns the source."], ["RAG", "Vector Search", "Python"], "chunker.split(text, overlap=ERROR_FRAGMENT_OVERLAP)"),
    ("llm-rate-limit", "ai", "Summary generation fails during a high-volume review session", "429 Too Many Requests", "The generation adapter retried all requests immediately instead of applying bounded backoff.", ["Separate retrieval success from summary generation failure.", "Apply bounded exponential backoff with jitter.", "Return cited results even when summary generation is unavailable."], ["LLM", "FastAPI", "SRE"], "Retry-After: <seconds>"),
    ("gpu-driver-mismatch", "ai", "GPU inference pod cannot start after node image update", "CUDA driver version is insufficient for CUDA runtime version", "The node driver stack was older than the container runtime expected.", ["Compare node driver, CUDA runtime, and framework versions.", "Schedule the workload on compatible GPU nodes.", "Pin the approved image/runtime combination."], ["CUDA", "Kubernetes", "AI"], "nvidia-smi && python -c \"import torch; print(torch.version.cuda)\""),
]

BLUEPRINT_EXPANSION_VARIANTS = [
    ("payments", "Payments workflow", "the payments API release path"),
    ("analytics", "Analytics workflow", "the analytics workspace refresh path"),
    ("identity", "Identity workflow", "the identity bridge login path"),
    ("knowledge", "Knowledge workflow", "the knowledge service review path"),
]

BLUEPRINT_EXPANSION_CASES = [
    (
        "lambda-subnet-ip-exhaustion",
        "cloud",
        "Lambda functions fail after VPC subnet expansion",
        "ENILimitReachedException",
        "The function created too many unique subnet and security-group combinations for the VPC attachment limit.",
        [
            "List function subnet and security-group combinations.",
            "Consolidate unnecessary combinations and remove stale versions.",
            "Request quota increase only after reducing configuration sprawl.",
        ],
        ["Lambda", "VPC", "AWS"],
        "aws lambda get-function-configuration --function-name <name>",
    ),
    (
        "api-gateway-integration-502",
        "cloud",
        "API Gateway returns 502 from a healthy backend",
        "Execution failed due to configuration error: Malformed Lambda proxy response",
        "The backend returned a body object instead of a JSON string in the proxy response contract.",
        [
            "Inspect the raw integration response in execution logs.",
            "Return statusCode, headers, and a stringified body.",
            "Add a contract test for success and error responses.",
        ],
        ["API Gateway", "Lambda", "Python"],
        "return {'statusCode': 200, 'body': json.dumps(payload)}",
    ),
    (
        "s3-presigned-clock-skew",
        "cloud",
        "S3 presigned uploads fail from one worker group",
        "SignatureDoesNotMatch",
        "The worker nodes generated signatures with a clock drift outside the accepted request window.",
        [
            "Compare node time against a trusted time source.",
            "Restart or repair time synchronization on the affected hosts.",
            "Regenerate the presigned URL and verify upload from the worker network.",
        ],
        ["S3", "AWS", "Linux"],
        "timedatectl status",
    ),
    (
        "iam-permission-boundary-deny",
        "cloud",
        "Deployment role is denied despite an attached allow policy",
        "AccessDenied: explicit deny in a permissions boundary",
        "The role permission boundary did not include the newly required service action.",
        [
            "Run policy simulation with the exact role and action.",
            "Update the boundary through the approved security review.",
            "Retest with the narrow target resource instead of wildcard access.",
        ],
        ["IAM", "AWS", "Security"],
        "aws iam simulate-principal-policy --policy-source-arn <role-arn> --action-names <action>",
    ),
    (
        "ecr-auth-token-expired",
        "cloud",
        "Container image push fails near the end of a long pipeline",
        "denied: Your authorization token has expired",
        "The pipeline authenticated to the registry before a long build and reused an expired token for push.",
        [
            "Move registry login closer to the push step.",
            "Fail fast when image build time exceeds token lifetime.",
            "Publish the image and verify the digest used by deployment.",
        ],
        ["Docker", "GitHub Actions", "AWS"],
        "aws ecr get-login-password | docker login --username AWS --password-stdin <registry>",
    ),
    (
        "eks-cni-ip-pressure",
        "cloud",
        "EKS node becomes NotReady after burst scheduling",
        "failed to assign an IP address to container",
        "The node subnet ran out of available pod IP addresses during the rollout.",
        [
            "Check CNI logs and subnet available IP count.",
            "Reduce burst scheduling or add approved subnet capacity.",
            "Validate pod networking after recycling affected nodes.",
        ],
        ["EKS", "Kubernetes", "VPC"],
        "kubectl -n kube-system logs ds/aws-node",
    ),
    (
        "helm-values-type-mismatch",
        "cloud",
        "Helm template renders an invalid manifest",
        "cannot unmarshal number into Go struct field EnvVar.value of type string",
        "A numeric value was supplied without quoting where Kubernetes expected a string environment value.",
        [
            "Render the chart locally with the target values file.",
            "Quote string-typed environment values in Helm templates.",
            "Run schema validation before applying the release.",
        ],
        ["Helm", "Kubernetes"],
        "helm template <release> <chart> -f values.yaml | kubectl apply --dry-run=server -f -",
    ),
    (
        "terraform-provider-region-drift",
        "cloud",
        "Terraform reads resources from the wrong account region",
        "NoSuchEntity: The role with name cannot be found",
        "A provider alias inherited the default region instead of the workload-specific region.",
        [
            "Inspect the provider block and module alias wiring.",
            "Pass the explicit provider alias into the child module.",
            "Run plan with account and region outputs enabled for review.",
        ],
        ["Terraform", "AWS", "IAM"],
        "terraform providers",
    ),
    (
        "cloudformation-export-in-use",
        "cloud",
        "CloudFormation cannot remove an old network output",
        "Export cannot be deleted as it is in use",
        "A dependent stack still imported the exported subnet value after the network refactor.",
        [
            "List imports for the export name.",
            "Update dependent stacks to the replacement value first.",
            "Remove the old export only after imports are zero.",
        ],
        ["CloudFormation", "AWS", "VPC"],
        "aws cloudformation list-imports --export-name <export>",
    ),
    (
        "route53-health-stale",
        "cloud",
        "Route 53 keeps sending traffic to a recovered endpoint",
        "health check status remains unhealthy",
        "The health check matched an old path that was removed during the service cutover.",
        [
            "Call the health-check path from outside the VPC.",
            "Update the check to the approved lightweight endpoint.",
            "Confirm DNS failover state after two healthy intervals.",
        ],
        ["Route 53", "AWS", "Nginx"],
        "aws route53 get-health-check-status --health-check-id <id>",
    ),
    (
        "grafana-datasource-tls",
        "sre",
        "Grafana panels fail after datasource certificate rotation",
        "x509: certificate signed by unknown authority",
        "The datasource container did not trust the internal certificate authority bundle.",
        [
            "Verify the certificate chain from the Grafana pod.",
            "Mount the approved CA bundle into the datasource client path.",
            "Restart the datasource and confirm dashboard queries recover.",
        ],
        ["Grafana", "Prometheus", "Linux"],
        "openssl s_client -connect <host>:443 -showcerts",
    ),
    (
        "loki-label-drop",
        "sre",
        "Loki cannot find logs after pipeline relabeling",
        "no labels matched selector",
        "The ingestion pipeline dropped the service label used by incident queries.",
        [
            "Inspect labels at the log shipper and Loki ingestion boundary.",
            "Restore the low-cardinality service label.",
            "Backfill only if retention and storage policy allow it.",
        ],
        ["Loki", "Grafana", "SRE"],
        "logcli labels service --since=1h",
    ),
    (
        "prometheus-scrape-unauthorized",
        "sre",
        "Prometheus scrape target turns unhealthy after auth change",
        "server returned HTTP status 401 Unauthorized",
        "The metrics endpoint started requiring a bearer token that the scrape job did not send.",
        [
            "Confirm the target response from the Prometheus network.",
            "Configure the approved scrape credential or expose a safe metrics path.",
            "Reload Prometheus and verify target health.",
        ],
        ["Prometheus", "Grafana", "Security"],
        "curl -i http://<target>/metrics",
    ),
    (
        "k8s-hpa-missing-metrics",
        "sre",
        "Horizontal pod autoscaler stops scaling during load",
        "failed to get cpu utilization: missing request for cpu",
        "The deployment omitted CPU requests, so the autoscaler could not compute utilization.",
        [
            "Inspect HPA events and deployment resource requests.",
            "Set measured CPU requests for the workload.",
            "Replay controlled load and verify scaling decisions.",
        ],
        ["Kubernetes", "Prometheus", "SRE"],
        "kubectl describe hpa <name>",
    ),
    (
        "node-inode-exhaustion",
        "sre",
        "Linux node has free disk but pods cannot write files",
        "No space left on device",
        "The filesystem exhausted inodes because temporary files were created without cleanup.",
        [
            "Check inode utilization separately from byte utilization.",
            "Remove only safe temporary files and fix the cleanup job.",
            "Add inode saturation alerts to node monitoring.",
        ],
        ["Linux", "Kubernetes", "Grafana"],
        "df -ih",
    ),
    (
        "otel-collector-memory-limiter",
        "sre",
        "OpenTelemetry collector restarts during traffic spikes",
        "memory_limiter processor refused data",
        "The collector accepted more spans than its memory limiter and batch settings could handle.",
        [
            "Inspect collector memory and dropped-span metrics.",
            "Tune batch size and memory limiter together.",
            "Apply tail sampling before scaling collector replicas.",
        ],
        ["OpenTelemetry", "Kubernetes", "SRE"],
        "otelcol_processor_refused_spans",
    ),
    (
        "alertmanager-route-shadow",
        "sre",
        "Critical alert is routed to the wrong receiver",
        "alert delivered to default receiver",
        "A broad parent route matched before the intended team-specific route.",
        [
            "Test the alert labels against the routing tree.",
            "Move the specific route before the broad fallback.",
            "Send a synthetic alert and verify receiver ownership.",
        ],
        ["Prometheus", "Grafana", "SRE"],
        "amtool config routes test --config.file alertmanager.yml severity=critical team=<team>",
    ),
    (
        "fastapi-validation-alias",
        "software",
        "FastAPI endpoint rejects a valid client payload",
        "422 Unprocessable Entity",
        "The API schema used a Python field name while the client sent the documented JSON alias.",
        [
            "Compare request JSON with the Pydantic schema aliases.",
            "Enable validated alias handling for the boundary model.",
            "Add integration tests for documented request fields.",
        ],
        ["FastAPI", "Python"],
        "model_config = ConfigDict(populate_by_name=True)",
    ),
    (
        "sqlalchemy-detached-instance",
        "software",
        "API serialization fails after session close",
        "DetachedInstanceError",
        "The response builder accessed a lazy relationship after the database session was closed.",
        [
            "Identify lazy fields used during serialization.",
            "Load required relationships inside the transaction boundary.",
            "Add a regression test that serializes after session cleanup.",
        ],
        ["SQLAlchemy", "FastAPI", "PostgreSQL"],
        "selectinload(Model.relationship)",
    ),
    (
        "node-esm-commonjs",
        "software",
        "Node.js worker fails after dependency upgrade",
        "ERR_REQUIRE_ESM",
        "A package changed to ESM-only while the worker still imported it through CommonJS require.",
        [
            "Identify the upgraded package entrypoint.",
            "Switch the worker import path to dynamic import or ESM.",
            "Run the packaged worker in the same Node version as production.",
        ],
        ["Node.js", "TypeScript"],
        "const mod = await import('package-name')",
    ),
    (
        "vite-public-env-prefix",
        "software",
        "Vite frontend builds without the configured API URL",
        "import.meta.env.VITE_API_BASE_URL is undefined",
        "The environment variable lacked the VITE_ prefix required for client exposure.",
        [
            "List build-time environment variables visible to Vite.",
            "Rename only public client configuration with the approved VITE_ prefix.",
            "Rebuild and confirm the generated bundle points to the expected API.",
        ],
        ["Vite", "React", "TypeScript"],
        "echo $VITE_API_BASE_URL && npm run build",
    ),
    (
        "react-hydration-theme",
        "software",
        "React page flashes and reports hydration mismatch",
        "Text content does not match server-rendered HTML",
        "Theme state was read from local storage during render before the client mounted.",
        [
            "Reproduce with a clean browser profile.",
            "Defer browser-only state until after mount.",
            "Add a visual regression for the initial render state.",
        ],
        ["React", "TypeScript"],
        "useEffect(() => setTheme(loadTheme()), [])",
    ),
    (
        "python-timezone-naive",
        "software",
        "Scheduled task runs an hour late after region change",
        "can't compare offset-naive and offset-aware datetimes",
        "The scheduler compared UTC-aware database timestamps with naive Python datetimes.",
        [
            "Trace timestamp creation and database serialization.",
            "Normalize all scheduler comparisons to timezone-aware UTC.",
            "Add tests around daylight-saving and region boundary dates.",
        ],
        ["Python", "FastAPI"],
        "datetime.now(UTC)",
    ),
    (
        "nginx-websocket-upgrade",
        "software",
        "Realtime client disconnects behind Nginx",
        "WebSocket connection failed: Error during WebSocket handshake",
        "The reverse proxy did not forward Upgrade and Connection headers to the upstream service.",
        [
            "Reproduce the handshake through the proxy.",
            "Add the required WebSocket upgrade headers.",
            "Run a long-lived connection smoke test after reload.",
        ],
        ["Nginx", "Node.js", "React"],
        "proxy_set_header Upgrade $http_upgrade;",
    ),
    (
        "redis-json-serialization",
        "software",
        "API fails to read cached profile data",
        "TypeError: Object of type UUID is not JSON serializable",
        "The cache writer stored raw Python objects instead of a stable JSON-safe representation.",
        [
            "Inspect the exact object written to cache.",
            "Serialize UUIDs and datetimes at the cache boundary.",
            "Clear affected keys and add a cache round-trip test.",
        ],
        ["Redis", "Python", "FastAPI"],
        "json.dumps(payload, default=str)",
    ),
    (
        "postgres-prepared-statement-stale",
        "software",
        "PostgreSQL queries fail after deploy with pooled connections",
        "cached plan must not change result type",
        "A migration changed a selected column type while pooled prepared statements stayed open.",
        [
            "Confirm the failure occurs only on existing pooled connections.",
            "Recycle application connections after the migration.",
            "Deploy a migration runbook that coordinates schema change and pool restart.",
        ],
        ["PostgreSQL", "SQLAlchemy", "FastAPI"],
        "DISCARD PLANS;",
    ),
    (
        "mysql-collation-mismatch",
        "software",
        "MySQL join fails after importing reference data",
        "Illegal mix of collations",
        "The imported table used a different collation than the application tables.",
        [
            "Compare collations for both joined columns.",
            "Convert the imported table to the approved database collation.",
            "Add import validation before loading reference data.",
        ],
        ["MySQL", "Python"],
        "SHOW FULL COLUMNS FROM <table>;",
    ),
    (
        "redis-cluster-moved",
        "sre",
        "Redis client fails after cluster resharding",
        "MOVED slot",
        "The client was configured as standalone Redis and did not follow cluster slot redirects.",
        [
            "Confirm cluster mode and slot ownership.",
            "Use a cluster-aware client configuration.",
            "Run read and write tests across multiple hash slots.",
        ],
        ["Redis", "SRE"],
        "redis-cli -c GET <key>",
    ),
    (
        "postgres-jsonb-index-miss",
        "software",
        "PostgreSQL JSON filter becomes slow after data growth",
        "query exceeded statement timeout",
        "The query filtered a JSONB path without a matching expression or GIN index.",
        [
            "Capture the query plan and filter selectivity.",
            "Add the narrow index that matches the actual predicate.",
            "Run analyze and verify the query uses the index.",
        ],
        ["PostgreSQL", "FastAPI"],
        "CREATE INDEX CONCURRENTLY ON events USING gin (payload);",
    ),
    (
        "mysql-packet-too-large",
        "data",
        "Bulk load into MySQL fails for wide rows",
        "Packet for query is too large",
        "The loader batched too many large JSON fields into one insert statement.",
        [
            "Measure the serialized batch size before insert.",
            "Reduce batch size and avoid unnecessary JSON payload duplication.",
            "Tune max packet size only within the approved database limit.",
        ],
        ["MySQL", "Python"],
        "SHOW VARIABLES LIKE 'max_allowed_packet';",
    ),
    (
        "airflow-provider-version-skew",
        "data",
        "Airflow DAG fails only on workers",
        "AttributeError: operator has no attribute",
        "Scheduler and worker images had different provider package versions.",
        [
            "Print provider versions from scheduler and worker containers.",
            "Build both images from the same locked dependency file.",
            "Clear failed task instances and rerun the affected DAG.",
        ],
        ["Airflow", "Python"],
        "airflow providers list",
    ),
    (
        "spark-schema-merge-conflict",
        "data",
        "Spark job fails while reading partitioned data",
        "Failed to merge incompatible data types",
        "One partition was written with a different column type during a backfill.",
        [
            "Identify the partition with the conflicting schema.",
            "Rewrite the partition with the canonical schema.",
            "Add schema validation before future backfills.",
        ],
        ["Spark", "Python"],
        "spark.read.parquet(path).printSchema()",
    ),
    (
        "dbt-incremental-unique-key",
        "data",
        "dbt incremental model creates duplicate business rows",
        "unique key is not unique",
        "The incremental unique key omitted the source-system identifier after a new feed was added.",
        [
            "Profile duplicates by the configured unique key.",
            "Include the source-system field in the incremental key.",
            "Run a full refresh in the controlled environment before promotion.",
        ],
        ["dbt", "PostgreSQL"],
        "dbt run --full-refresh --select <model>",
    ),
    (
        "kafka-schema-registry-subject",
        "data",
        "Kafka producer is rejected after schema evolution",
        "Schema being registered is incompatible with an earlier schema",
        "The producer changed a required field without a compatible default.",
        [
            "Check the subject compatibility mode.",
            "Add a backward-compatible field default or versioned topic contract.",
            "Replay a sample event through producer and consumer validation.",
        ],
        ["Kafka", "Python"],
        "curl <schema-registry>/subjects/<subject>/versions/latest",
    ),
    (
        "airflow-pool-starvation",
        "data",
        "Airflow DAG stalls while unrelated tasks keep running",
        "Task is queued but not running",
        "All slots in the assigned pool were consumed by long-running backfill tasks.",
        [
            "Inspect pool occupancy and queued tasks.",
            "Move backfills into a separate bounded pool.",
            "Set pool alerts when critical DAGs cannot acquire slots.",
        ],
        ["Airflow", "SRE"],
        "airflow pools list",
    ),
    (
        "spark-driver-result-size",
        "data",
        "Spark driver fails after collect in validation job",
        "Total size of serialized results is bigger than spark.driver.maxResultSize",
        "The validation code collected a large distributed dataset to the driver.",
        [
            "Find collect or toPandas calls in the validation path.",
            "Aggregate in Spark before returning small results to the driver.",
            "Add a data-size guard to prevent unbounded collection.",
        ],
        ["Spark", "Python"],
        "df.groupBy('status').count().show()",
    ),
    (
        "vector-dimension-mismatch",
        "ai",
        "Vector insert fails after embedding model switch",
        "expected 1024 dimensions, not 1536",
        "Existing pgvector storage was sized for the previous embedding model.",
        [
            "Confirm configured embedding model and output dimension.",
            "Create a migration plan for vector column dimension and re-embedding.",
            "Block mixed-dimension writes with a startup validation check.",
        ],
        ["Vector Search", "RAG", "PostgreSQL"],
        "SELECT vector_dims(embedding) FROM solution_embeddings LIMIT 1;",
    ),
    (
        "rag-citation-contract",
        "ai",
        "Grounded summary is rejected by validation",
        "citation list contains unknown solution id",
        "The model cited an identifier that was not present in the authorized source set.",
        [
            "Reject the generated response without displaying it.",
            "Retry with the allowed source identifiers only.",
            "Add an evaluation case for citation validation.",
        ],
        ["RAG", "LLM", "FastAPI"],
        "assert set(answer.citations) <= allowed_solution_ids",
    ),
    (
        "llm-context-window-truncation",
        "ai",
        "LLM summary misses the highest ranked solution",
        "maximum context length exceeded",
        "The context builder included too many low-ranked records before the strongest evidence.",
        [
            "Sort authorized eligible records globally before context assembly.",
            "Limit context by ranked source count and token budget.",
            "Verify the top record remains present in the prompt.",
        ],
        ["LLM", "RAG", "Python"],
        "sources = ranked_sources[:RAG_MAX_CONTEXT_SOLUTIONS]",
    ),
    (
        "mlflow-artifact-access",
        "ai",
        "Model registration cannot read evaluation artifacts",
        "Permission denied while downloading artifact",
        "The MLflow artifact store policy allowed the training role but not the registration role.",
        [
            "Identify the artifact URI and caller role.",
            "Grant read access to the registration role through the approved policy.",
            "Rerun registration and verify artifact lineage is preserved.",
        ],
        ["MLflow", "AWS", "Security"],
        "mlflow artifacts download --artifact-uri <uri>",
    ),
]

for variant_key, variant_title, workload_context in BLUEPRINT_EXPANSION_VARIANTS:
    for key, domain, title, error, root_cause, steps, technologies, code in BLUEPRINT_EXPANSION_CASES:
        BLUEPRINTS.append(
            (
                f"{key}-{variant_key}",
                domain,
                f"{title} - {variant_title}",
                error,
                f"{root_cause} The issue surfaced in {workload_context}.",
                steps,
                technologies,
                code,
            )
        )

ENVIRONMENTS = [
    ("Development", "ap-south-1", "dev"),
    ("Integration", "ap-south-1", "int"),
    ("UAT", "ap-south-1", "uat"),
    ("Staging", "eu-west-1", "stage"),
    ("Pre-production", "eu-west-1", "preprod"),
    ("Production", "eu-west-1", "prod"),
    ("Disaster recovery", "ap-southeast-1", "dr"),
]

SERVICE_CONTEXTS = [
    ("payments API", "release pipeline", "customer checkout path"),
    ("claims ingestion", "batch processing window", "downstream reporting feed"),
    ("analytics workspace", "model evaluation run", "data-science notebook users"),
    ("platform gateway", "blue-green rollout", "internal service consumers"),
    ("migration control plane", "cutover rehearsal", "cloud operations team"),
    ("observability stack", "incident response room", "on-call engineers"),
    ("knowledge service", "review workflow", "solution authors and reviewers"),
    ("identity bridge", "login and token refresh path", "authenticated employees"),
]

DOMAIN_TEAM = {"cloud": "cloud_engineering", "sre": "sreaas", "software": "software_engineering", "data": "software_engineering", "ai": "ai_engineering"}
REVIEWER_TEAMS = {"cloud": ["cloud_management", "platform_leadership"], "sre": ["sreaas", "cloud_management"], "software": ["ida_management"], "data": ["ida_management"], "ai": ["ai_management"]}


def main() -> None:
    with SessionLocal() as db:
        department_ids = {}
        for slug, name in DEPARTMENTS.items():
            identifier = stable_id(f"department/{slug}")
            department = db.get(Department, identifier)
            if department is None:
                department = first_by_unique(db, Department, Department.slug == slug)
            if department is None:
                department = first_by_unique(db, Department, Department.name == name)
            if department is None:
                department = Department(id=identifier, name=name, slug=slug)
                db.add(department)
            else:
                department.name = name
                department.slug = slug
            department_ids[slug] = department.id
        db.flush()

        team_ids = {}
        for key, (name, department_slug) in TEAMS.items():
            identifier = stable_id(f"team/{key}")
            team = db.get(Team, identifier)
            if team is None:
                team = first_by_unique(db, Team, Team.slug == key.replace("_", "-"))
            if team is None:
                team = first_by_unique(db, Team, Team.department_id == department_ids[department_slug], Team.name == name)
            if team is None:
                team = Team(id=identifier, department_id=department_ids[department_slug], name=name, slug=key.replace("_", "-"))
                db.add(team)
            else:
                team.department_id = department_ids[department_slug]
                team.name = name
                team.slug = key.replace("_", "-")
            team_ids[key] = team.id
        db.flush()

        technology_ids = {}
        for name, category in TECHNOLOGIES:
            slug = name.lower().replace(" ", "-").replace(".", "")
            identifier = stable_id(f"technology/{slug}")
            technology = db.get(Technology, identifier)
            if technology is None:
                technology = first_by_unique(db, Technology, Technology.slug == slug)
            if technology is None:
                technology = first_by_unique(db, Technology, Technology.name == name)
            if technology is None:
                technology = Technology(id=identifier, name=name, slug=slug, category=category)
                db.add(technology)
            else:
                technology.name = name
                technology.slug = slug
                technology.category = category
            technology_ids[name] = technology.id
        db.flush()

        password_hash = hash_password("development-only-password")
        people: dict[str, User] = {}
        people_by_team: dict[str, list[User]] = {key: [] for key in TEAMS}
        employee_meta = {}
        for name, title, team_key, role, skills in EMPLOYEES:
            identifier = stable_person_id(name)
            email = email_for(name)
            user = db.get(User, identifier)
            if user is None:
                user = first_by_unique(db, User, User.email == email)
            if user is None:
                user = User(id=identifier, email=email, password_hash=password_hash, role=role, is_active=True)
                db.add(user)
            else:
                user.email = email
                user.password_hash = password_hash
                user.role = role
                user.is_active = True
            people[name] = user
            people_by_team[team_key].append(user)
            department_slug = TEAMS[team_key][1]
            profile = db.get(EmployeeProfile, identifier)
            bio = f"{title} working across {', '.join(skills[:3])}."
            if profile is None:
                db.add(EmployeeProfile(
                    user_id=identifier,
                    display_name=name,
                    job_title=title,
                    department_id=department_ids[department_slug],
                    team_id=team_ids[team_key],
                    contact_email=email,
                    contact_handle=f"@{email.split('@')[0]}",
                    skills=skills,
                    bio=bio,
                    avatar_key=None,
                ))
            else:
                profile.display_name = name
                profile.job_title = title
                profile.department_id = department_ids[department_slug]
                profile.team_id = team_ids[team_key]
                profile.contact_email = email
                profile.contact_handle = f"@{email.split('@')[0]}"
                profile.skills = skills
                profile.bio = bio
            employee_meta[identifier] = (team_key, role)
        db.flush()

        owner_pools = {
            domain: people_by_team[team_key]
            for domain, team_key in DOMAIN_TEAM.items()
        }
        reviewer_pools = {
            domain: [user for team_key in teams for user in people_by_team[team_key]]
            for domain, teams in REVIEWER_TEAMS.items()
        }
        all_users = list(people.values())

        solution_count = 0
        verified_count = 0
        for blueprint_index, (key, domain, title, error, root_cause, steps, technologies, code) in enumerate(BLUEPRINTS):
            for environment_index, (environment_name, region, environment_slug) in enumerate(ENVIRONMENTS):
                index = blueprint_index * len(ENVIRONMENTS) + environment_index
                owner_pool = owner_pools[domain]
                owner = owner_pool[index % len(owner_pool)]
                owner_team_key, _ = employee_meta[owner.id]
                department_slug = TEAMS[owner_team_key][1]
                challenge_id = stable_id(f"challenge/{key}/{environment_slug}")
                solution_id = stable_id(f"solution/{key}/{environment_slug}")
                status = ContentStatus.VERIFIED if index % 12 not in {10, 11} else ContentStatus.SUBMITTED if index % 12 == 10 else ContentStatus.DRAFT
                visibility = VisibilityLevel.COMPANY
                if index % 13 == 0:
                    visibility = VisibilityLevel.DEPARTMENT
                elif index % 17 == 0:
                    visibility = VisibilityLevel.TEAM
                service_name, operation_name, affected_users = SERVICE_CONTEXTS[index % len(SERVICE_CONTEXTS)]
                problem = (
                    f"During the {operation_name} for the {service_name} in {environment_name.lower()} ({region}), "
                    f"the team observed: {title.lower()}. The issue affected {affected_users} and was documented "
                    "as a reusable internal runbook after the fix was verified."
                )
                symptoms = (
                    f"The service reported `{error}`. The team confirmed the failure through logs, health checks, "
                    f"or deployment events before correcting the underlying {domain} control."
                )
                environment = f"{environment_name} | {region} | Cloud migration wave {(index % 8) + 1}"
                challenge = db.get(Challenge, challenge_id)
                if challenge is None:
                    challenge = Challenge(
                        id=challenge_id,
                        title=f"{title} - {environment_name}",
                        problem_description=problem,
                        symptoms=symptoms,
                        exact_error_message=error,
                        environment=environment,
                        status=status,
                        visibility=visibility,
                        department_id=department_ids[department_slug],
                        team_id=team_ids[owner_team_key],
                        owner_user_id=owner.id,
                        created_by_user_id=owner.id,
                        updated_by_user_id=owner.id,
                    )
                    db.add(challenge)
                else:
                    challenge.title = f"{title} - {environment_name}"
                    challenge.problem_description = problem
                    challenge.symptoms = symptoms
                    challenge.exact_error_message = error
                    challenge.environment = environment
                    challenge.status = status
                    challenge.visibility = visibility
                    challenge.department_id = department_ids[department_slug]
                    challenge.team_id = team_ids[owner_team_key]
                    challenge.owner_user_id = owner.id
                    challenge.updated_by_user_id = owner.id

                solution = db.get(Solution, solution_id)
                resolution = [
                    f"{step} ({environment_name} validation)." if not step.endswith(".") else f"{step[:-1]} ({environment_name} validation)."
                    for step in steps
                ]
                prevention = (
                    f"Added a pre-change check for {service_name}, an owner-reviewed rollback note, "
                    f"and an alert or validation step covering the {', '.join(technologies[:2])} control."
                )
                if solution is None:
                    solution = Solution(
                        id=solution_id,
                        challenge_id=challenge_id,
                        root_cause=root_cause,
                        resolution_steps=resolution,
                        code_snippets=[code] if code else [],
                        prevention_notes=prevention,
                        status=status,
                        solved_at=date.today() - timedelta(days=(index % 240) + 1),
                        primary_owner_user_id=owner.id,
                    )
                    db.add(solution)
                else:
                    solution.root_cause = root_cause
                    solution.resolution_steps = resolution
                    solution.code_snippets = [code] if code else []
                    solution.prevention_notes = prevention
                    solution.status = status
                    solution.primary_owner_user_id = owner.id

                for technology_name in technologies:
                    technology_id = technology_ids.get(technology_name)
                    if technology_id is None:
                        continue
                    link = db.get(ChallengeTechnology, {"challenge_id": challenge_id, "technology_id": technology_id})
                    if link is None:
                        db.add(ChallengeTechnology(challenge_id=challenge_id, technology_id=technology_id))

                if status == ContentStatus.VERIFIED:
                    db.flush()
                    verified_count += 1
                    reviewers = reviewer_pools[domain]
                    reviewer = reviewers[index % len(reviewers)]
                    review_id = stable_id(f"review/{key}/{environment_slug}")
                    if db.get(VerificationReview, review_id) is None:
                        db.add(VerificationReview(
                            id=review_id,
                            solution_id=solution_id,
                            reviewer_user_id=reviewer.id,
                            decision=ReviewDecision.VERIFIED,
                            notes="Validated against the documented migration environment and approved as a reusable solution.",
                            visibility_after=visibility,
                        ))

                    # A small amount of deterministic feedback makes contributor and ranking views useful.
                    if index % 3 == 0:
                        for feedback_offset, value in enumerate((FeedbackValue.HELPFUL, FeedbackValue.RESOLVED_MY_ISSUE)):
                            submitter = all_users[(index + feedback_offset + 7) % len(all_users)]
                            if submitter.id == owner.id:
                                submitter = all_users[(index + feedback_offset + 9) % len(all_users)]
                            feedback_id = stable_id(f"feedback/{key}/{environment_slug}/{feedback_offset}")
                            if db.get(Feedback, feedback_id) is None:
                                db.add(Feedback(
                                    id=feedback_id,
                                    solution_id=solution_id,
                                    submitted_by_user_id=submitter.id,
                                    value=value,
                                    comment="The documented steps were clear and reusable." if value == FeedbackValue.HELPFUL else "The solution resolved the incident.",
                                ))
                solution_count += 1

        db.commit()
        status_counts = {status.value: db.query(Challenge).filter(Challenge.status == status).count() for status in ContentStatus}

    print(
        f"Minfy Resolve showcase corpus ready: {len(EMPLOYEES)} employees, "
        f"{solution_count} generated solutions ({verified_count} verified); statuses={status_counts}."
    )
    print("Seeded local access profiles were refreshed.")


if __name__ == "__main__":
    main()
