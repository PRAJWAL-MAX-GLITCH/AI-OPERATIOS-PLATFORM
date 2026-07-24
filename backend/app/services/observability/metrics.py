"""
Observability Metrics
=====================
Prometheus metrics registry and collection for the Enterprise AI Operations Platform.
"""
from prometheus_client import Counter, Histogram, Gauge

# --- API & Application Metrics ---
HTTP_REQUESTS_TOTAL = Counter(
    "http_requests_total",
    "Total number of HTTP requests",
    ["method", "endpoint", "status_code"]
)

HTTP_REQUEST_DURATION_SECONDS = Histogram(
    "http_request_duration_seconds",
    "HTTP request duration in seconds",
    ["method", "endpoint"]
)

ACTIVE_USERS = Gauge(
    "active_users_total",
    "Number of active users online"
)

CONCURRENT_REQUESTS = Gauge(
    "concurrent_requests",
    "Number of currently processing requests"
)

# --- Database Metrics ---
DB_CONNECTIONS = Gauge(
    "db_connections_active",
    "Number of active database connections"
)

DB_QUERIES_TOTAL = Counter(
    "db_queries_total",
    "Total number of database queries executed",
    ["type"]
)

DB_QUERY_DURATION_SECONDS = Histogram(
    "db_query_duration_seconds",
    "Database query duration in seconds",
    ["type"]
)

DB_FAILURES_TOTAL = Counter(
    "db_failures_total",
    "Total number of database query failures"
)

# --- ML Metrics ---
ML_TRAINING_JOBS_TOTAL = Counter(
    "ml_training_jobs_total",
    "Total number of ML training jobs",
    ["status"]
)

ML_EVALUATION_JOBS_TOTAL = Counter(
    "ml_evaluation_jobs_total",
    "Total number of ML evaluation jobs",
    ["status"]
)

PREDICTION_COUNT_TOTAL = Counter(
    "ml_prediction_requests_total",
    "Total number of prediction requests",
    ["model_version_id"]
)

INFERENCE_LATENCY_SECONDS = Histogram(
    "ml_inference_latency_seconds",
    "Inference latency in seconds",
    ["model_version_id"]
)

# --- RAG Metrics ---
RAG_DOCUMENTS_INDEXED_TOTAL = Counter(
    "rag_documents_indexed_total",
    "Total number of documents indexed into vector DB"
)

RAG_EMBEDDING_TIME_SECONDS = Histogram(
    "rag_embedding_time_seconds",
    "Time taken to generate embeddings in seconds"
)

RAG_RETRIEVAL_LATENCY_SECONDS = Histogram(
    "rag_retrieval_latency_seconds",
    "Latency of vector similarity search in seconds"
)

RAG_CACHE_HITS_TOTAL = Counter(
    "rag_cache_hits_total",
    "Total number of semantic cache hits"
)

RAG_SEARCH_ACCURACY = Gauge(
    "rag_search_accuracy_score",
    "Placeholder for semantic search accuracy tracking"
)

# --- Agent Metrics ---
AGENT_RUNS_TOTAL = Counter(
    "agent_runs_total",
    "Total number of agent executions",
    ["agent_type", "status"]
)

AGENT_TOOL_CALLS_TOTAL = Counter(
    "agent_tool_calls_total",
    "Total number of tools called by agents",
    ["tool_name"]
)

AGENT_EXECUTION_TIME_SECONDS = Histogram(
    "agent_execution_time_seconds",
    "Agent task execution time in seconds",
    ["agent_type"]
)

# --- Workflow Metrics ---
WORKFLOW_RUNS_TOTAL = Counter(
    "workflow_runs_total",
    "Total number of workflow runs",
    ["workflow_name", "status"]
)

WORKFLOW_TASK_STATUS_TOTAL = Counter(
    "workflow_task_status_total",
    "Workflow task execution statuses",
    ["task_type", "status"]
)

WORKFLOW_TASK_RETRIES_TOTAL = Counter(
    "workflow_task_retries_total",
    "Total retries for workflow tasks",
    ["task_type"]
)

WORKFLOW_QUEUE_LENGTH = Gauge(
    "workflow_celery_queue_length",
    "Current length of the celery background task queue"
)
