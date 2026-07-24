/**
 * Shared agent-domain constants.
 * Mirrors the backend AgentRegistry registrations.
 */

export const AGENT_META = {
  planner: {
    label: 'Planner Agent',
    description: 'Orchestrates complex multi-step goals by decomposing them into subtasks and delegating to specialist agents.',
    icon: '🗺️',
    color: 'indigo',
    capabilities: ['Goal decomposition', 'Agent delegation', 'Plan synthesis'],
    tools: [],
  },
  dataset_analyst: {
    label: 'Dataset Analyst',
    description: 'Profiles uploaded datasets: statistics, missing values, schema, quality score, and anomaly detection.',
    icon: '📊',
    color: 'blue',
    capabilities: ['Column profiling', 'Quality scoring', 'Outlier detection'],
    tools: ['get_dataset_stats'],
  },
  ml_engineer: {
    label: 'ML Engineer',
    description: 'Recommends algorithms, preprocessing steps, evaluation metrics, and training strategies for your problem.',
    icon: '⚙️',
    color: 'violet',
    capabilities: ['Algorithm selection', 'Preprocessing advice', 'Metric recommendations'],
    tools: ['lookup_experiment_models'],
  },
  rag_researcher: {
    label: 'RAG Researcher',
    description: 'Searches your enterprise knowledge base using semantic retrieval and provides cited answers.',
    icon: '🔎',
    color: 'emerald',
    capabilities: ['Semantic search', 'Document summarisation', 'Citation generation'],
    tools: ['search_documents'],
  },
  report_generator: {
    label: 'Report Generator',
    description: 'Synthesises multi-agent findings into structured Markdown reports with sections and recommendations.',
    icon: '📝',
    color: 'amber',
    capabilities: ['Markdown generation', 'Finding synthesis', 'Executive summaries'],
    tools: [],
  },
};

export const AGENT_COLORS = {
  indigo: { bg: 'bg-indigo-50', text: 'text-indigo-700', border: 'border-indigo-200', dot: 'bg-indigo-500' },
  blue:   { bg: 'bg-blue-50',   text: 'text-blue-700',   border: 'border-blue-200',   dot: 'bg-blue-500' },
  violet: { bg: 'bg-violet-50', text: 'text-violet-700', border: 'border-violet-200', dot: 'bg-violet-500' },
  emerald:{ bg: 'bg-emerald-50',text: 'text-emerald-700',border: 'border-emerald-200',dot: 'bg-emerald-500' },
  amber:  { bg: 'bg-amber-50',  text: 'text-amber-700',  border: 'border-amber-200',  dot: 'bg-amber-500' },
};

export const STATUS_META = {
  pending:   { label: 'Pending',    color: 'text-yellow-700 bg-yellow-100',  dot: 'bg-yellow-400' },
  running:   { label: 'Running',    color: 'text-blue-700 bg-blue-100',      dot: 'bg-blue-500 animate-pulse' },
  completed: { label: 'Completed',  color: 'text-green-700 bg-green-100',    dot: 'bg-green-500' },
  failed:    { label: 'Failed',     color: 'text-red-700 bg-red-100',        dot: 'bg-red-500' },
  cancelled: { label: 'Cancelled',  color: 'text-gray-700 bg-gray-100',      dot: 'bg-gray-400' },
};

export const ROLE_META = {
  thought:     { label: 'Thought',      icon: '💭', color: 'text-purple-700 bg-purple-50 border-purple-200' },
  action:      { label: 'Tool Call',    icon: '🔧', color: 'text-blue-700 bg-blue-50 border-blue-200' },
  observation: { label: 'Observation',  icon: '👁️',  color: 'text-teal-700 bg-teal-50 border-teal-200' },
  final:       { label: 'Final Answer', icon: '✅', color: 'text-green-700 bg-green-50 border-green-200' },
  error:       { label: 'Error',        icon: '❌', color: 'text-red-700 bg-red-50 border-red-200' },
};

export const EXAMPLE_PROMPTS = {
  planner: [
    'Analyze our Q4 churn dataset and recommend the best model to deploy.',
    'Research transformer architecture documents and produce an executive report.',
    'Profile the sales data, train a forecasting model, and summarize results.',
  ],
  dataset_analyst: [
    'Analyze this customer churn dataset and identify data quality issues.',
    'Profile the uploaded sales figures and report missing values.',
    'Summarise the schema and feature types of the latest dataset.',
  ],
  ml_engineer: [
    'Recommend the best algorithm for binary classification on this dataset.',
    'What preprocessing steps should I apply before training?',
    'Which metrics should I use to evaluate this regression problem?',
  ],
  rag_researcher: [
    'Search our documents for information about transformer attention mechanisms.',
    'Find any mentions of PostgreSQL performance tuning in our knowledge base.',
    'What do our internal reports say about annual revenue trends?',
  ],
  report_generator: [
    'Generate an executive summary based on the Q4 analysis findings.',
    'Write a technical report comparing model performance across experiments.',
    'Produce a risk assessment report for the proposed ML deployment.',
  ],
};

/** Active statuses that should trigger polling */
export const ACTIVE_STATUSES = new Set(['pending', 'running']);
