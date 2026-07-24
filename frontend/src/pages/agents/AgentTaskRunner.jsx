/**
 * Agent Task Runner / Execution View — /agents/tasks/:taskId
 *
 * Shows live execution status, planner steps, tool calls,
 * agent-to-agent handoffs, timeline, output, and memory.
 * Polls every 3 seconds while task is active.
 */
import { useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  ChevronLeft, RefreshCw, XCircle, AlertCircle, CheckCircle2,
  Clock, Wrench, MessageSquare, ChevronDown, ChevronUp, Copy,
  Check, Loader2, ArrowRight, FileText, Bot, Play,
} from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '../../components/ui/Card';
import { Button } from '../../components/ui/Button';
import { fetchTaskStatus, fetchTaskRuns, cancelTask } from '../../services/agentApi';
import { AGENT_META, STATUS_META, ROLE_META, ACTIVE_STATUSES } from '../../services/agentConstants';
import { formatDistanceToNow, format } from 'date-fns';
import ReactMarkdown from './ReactMarkdownShim';

// ── Sub-components ─────────────────────────────────────────────────────────────

function StatusBadge({ status, large = false }) {
  const meta = STATUS_META[status] ?? STATUS_META.pending;
  return (
    <span className={`inline-flex items-center gap-1.5 rounded-full font-medium ${large ? 'px-3 py-1 text-sm' : 'px-2.5 py-0.5 text-xs'} ${meta.color}`}>
      <span className={`rounded-full flex-shrink-0 ${large ? 'w-2 h-2' : 'w-1.5 h-1.5'} ${meta.dot}`} />
      {meta.label}
    </span>
  );
}

function CopyButton({ text }) {
  const [copied, setCopied] = useState(false);
  const handleCopy = () => {
    navigator.clipboard.writeText(text).then(() => {
      setCopied(true);
      setTimeout(() => setCopied(false), 1800);
    });
  };
  return (
    <button
      onClick={handleCopy}
      className="p-1 rounded hover:bg-gray-100 transition-colors text-gray-400 hover:text-gray-700"
      aria-label="Copy to clipboard"
    >
      {copied ? <Check className="w-3.5 h-3.5 text-green-600" /> : <Copy className="w-3.5 h-3.5" />}
    </button>
  );
}

function MessageCard({ msg, index }) {
  const role = ROLE_META[msg.role] ?? ROLE_META.thought;
  const [expanded, setExpanded] = useState(msg.role === 'final' || index === 0);

  return (
    <div className={`rounded-lg border p-3 ${role.color}`}>
      <button
        type="button"
        className="w-full flex items-center justify-between gap-2 text-left"
        onClick={() => setExpanded(!expanded)}
        aria-expanded={expanded}
      >
        <div className="flex items-center gap-2 text-sm font-medium">
          <span>{role.icon}</span>
          <span>
            {role.label}
            {msg.tool_name && <span className="ml-2 font-mono text-xs opacity-70">({msg.tool_name})</span>}
          </span>
          {msg.created_at && (
            <span className="font-normal text-xs opacity-60 ml-2">
              {format(new Date(msg.created_at), 'HH:mm:ss')}
            </span>
          )}
        </div>
        <div className="flex items-center gap-1">
          <CopyButton text={msg.content} />
          {expanded ? <ChevronUp className="w-3.5 h-3.5" /> : <ChevronDown className="w-3.5 h-3.5" />}
        </div>
      </button>

      {expanded && (
        <div className="mt-2 text-sm space-y-2">
          {/* Main content */}
          <div className="whitespace-pre-wrap font-mono text-xs leading-relaxed opacity-90">
            {msg.content}
          </div>

          {/* Tool input */}
          {msg.tool_input && (
            <div>
              <div className="text-xs font-semibold opacity-60 mt-2 mb-1 flex items-center gap-1">
                <Wrench className="w-3 h-3" /> Input
              </div>
              <pre className="text-xs rounded bg-black/5 p-2 overflow-x-auto">
                {JSON.stringify(msg.tool_input, null, 2)}
              </pre>
            </div>
          )}

          {/* Tool output — never expose secrets, just the value */}
          {msg.tool_output && (
            <div>
              <div className="text-xs font-semibold opacity-60 mt-2 mb-1 flex items-center gap-1">
                <ArrowRight className="w-3 h-3" /> Output
              </div>
              <pre className="text-xs rounded bg-black/5 p-2 overflow-x-auto whitespace-pre-wrap">
                {msg.tool_output}
              </pre>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

function PlannerSteps({ messages }) {
  // Extract planner-style steps: thoughts and actions form the plan
  const steps = messages.filter((m) => ['thought', 'action', 'observation', 'final'].includes(m.role));
  if (steps.length === 0) return null;

  const stepStatus = (role) => {
    if (role === 'final')       return { icon: <CheckCircle2 className="w-4 h-4 text-green-600" />, bg: 'bg-green-100 border-green-200' };
    if (role === 'action')      return { icon: <Wrench className="w-4 h-4 text-blue-600" />,        bg: 'bg-blue-50 border-blue-200' };
    if (role === 'observation') return { icon: <MessageSquare className="w-4 h-4 text-teal-600" />, bg: 'bg-teal-50 border-teal-200' };
    return                             { icon: <MessageSquare className="w-4 h-4 text-purple-600" />,bg: 'bg-purple-50 border-purple-200' };
  };

  return (
    <div className="space-y-2">
      {steps.map((step, i) => {
        const { icon, bg } = stepStatus(step.role);
        return (
          <div key={i} className="flex gap-3 items-start">
            <div className="flex-shrink-0 mt-0.5">
              <div className={`w-6 h-6 rounded-full border flex items-center justify-center ${bg}`}>{icon}</div>
            </div>
            {i < steps.length - 1 && (
              <div className="absolute left-[11px] mt-6 w-0.5 h-4 bg-gray-200" />
            )}
            <div className="flex-1 min-w-0">
              <div className="text-xs font-semibold text-gray-500 uppercase tracking-wide">
                {ROLE_META[step.role]?.label ?? step.role}
                {step.tool_name && <span className="ml-1 font-mono normal-case">— {step.tool_name}</span>}
              </div>
              <p className="text-sm text-gray-700 mt-0.5 line-clamp-2">{step.content}</p>
            </div>
          </div>
        );
      })}
    </div>
  );
}

function ToolCallsTable({ messages }) {
  const toolMessages = messages.filter((m) => m.role === 'action' && m.tool_name);
  if (toolMessages.length === 0) return <p className="text-sm text-gray-400">No tool calls in this run.</p>;

  return (
    <div className="overflow-x-auto">
      <table className="w-full text-sm">
        <thead>
          <tr className="text-left text-xs text-gray-500 border-b">
            <th className="pb-2 font-medium">#</th>
            <th className="pb-2 font-medium">Tool</th>
            <th className="pb-2 font-medium">Time</th>
            <th className="pb-2 font-medium">Status</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-gray-100">
          {toolMessages.map((m, i) => (
            <tr key={i} className="hover:bg-gray-50">
              <td className="py-2 text-gray-400">{i + 1}</td>
              <td className="py-2">
                <span className="font-mono text-indigo-700 text-xs bg-indigo-50 px-2 py-0.5 rounded">
                  {m.tool_name}
                </span>
              </td>
              <td className="py-2 text-gray-400 text-xs">
                {m.created_at ? format(new Date(m.created_at), 'HH:mm:ss') : '—'}
              </td>
              <td className="py-2">
                <span className="text-xs text-green-700 bg-green-50 px-2 py-0.5 rounded-full">called</span>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function AgentHandoffTimeline({ runs }) {
  if (!runs || runs.length < 2) return null;
  return (
    <div className="flex items-center gap-2 flex-wrap">
      {runs.map((run, i) => {
        const meta = AGENT_META[run.agent_type] ?? { icon: '🤖', label: run.agent_type };
        return (
          <div key={run.run_id} className="flex items-center gap-2">
            <div className="flex items-center gap-1.5 px-3 py-1.5 bg-gray-50 border border-gray-200 rounded-lg text-sm">
              <span>{meta.icon}</span>
              <span className="font-medium">{meta.label}</span>
              <span className={`w-2 h-2 rounded-full ${STATUS_META[run.status]?.dot ?? 'bg-gray-400'}`} />
            </div>
            {i < runs.length - 1 && <ArrowRight className="w-4 h-4 text-gray-300" />}
          </div>
        );
      })}
    </div>
  );
}

function FinalOutput({ result, errorMessage, status }) {
  if (status === 'failed') {
    const safe = getFriendlyError(errorMessage);
    return (
      <div className="rounded-lg border border-red-200 bg-red-50 p-4">
        <div className="flex items-center gap-2 mb-2">
          <XCircle className="w-5 h-5 text-red-600" />
          <h3 className="font-semibold text-red-800">Task Failed</h3>
        </div>
        <p className="text-sm text-red-700">{safe}</p>
      </div>
    );
  }

  if (status === 'cancelled') {
    return (
      <div className="rounded-lg border border-gray-200 bg-gray-50 p-4 text-sm text-gray-600">
        Task was cancelled.
      </div>
    );
  }

  if (!result?.answer) return null;

  return (
    <div className="rounded-lg border border-green-200 bg-green-50 p-4">
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          <CheckCircle2 className="w-5 h-5 text-green-600" />
          <h3 className="font-semibold text-green-800">Result</h3>
        </div>
        <CopyButton text={result.answer} />
      </div>
      <div className="prose prose-sm prose-green max-w-none text-green-900 text-sm whitespace-pre-wrap font-mono leading-relaxed">
        {result.answer}
      </div>
    </div>
  );
}

/** Map backend errors to safe user-facing messages */
function getFriendlyError(msg) {
  if (!msg) return 'An unexpected error occurred.';
  if (msg.toLowerCase().includes('timeout'))        return 'The agent timed out. Try a simpler task or contact support.';
  if (msg.toLowerCase().includes('api key'))        return 'LLM provider is unavailable. Please check your API key configuration.';
  if (msg.toLowerCase().includes('permission'))     return 'You do not have permission to access the required resource.';
  if (msg.toLowerCase().includes('max_steps'))      return 'The agent reached the maximum number of steps without completing the task.';
  if (msg.toLowerCase().includes('dataset'))        return 'The required dataset was not found or is unavailable.';
  if (msg.toLowerCase().includes('retrieval'))      return 'RAG knowledge base retrieval failed. Check your index.';
  if (msg.toLowerCase().includes('cancelled'))      return 'Task was cancelled by user.';
  // Generic fallback — don't expose stack traces
  return 'The agent encountered an error during execution.';
}

// ── Main Component ─────────────────────────────────────────────────────────────

export default function AgentTaskRunner() {
  const { taskId } = useParams();
  const navigate = useNavigate();
  const qc = useQueryClient();
  const [activeTab, setActiveTab] = useState('timeline');
  const [cancelConfirm, setCancelConfirm] = useState(false);

  // ── Task status polling ──
  const taskQ = useQuery({
    queryKey: ['task-status', taskId],
    queryFn: () => fetchTaskStatus(taskId),
    refetchInterval: (data) => {
      const status = data?.state?.data?.status ?? data?.status;
      return ACTIVE_STATUSES.has(status) ? 3000 : false;
    },
    staleTime: 1000,
  });

  // ── Run details (messages) polling ──
  const runsQ = useQuery({
    queryKey: ['task-runs', taskId],
    queryFn: () => fetchTaskRuns(taskId),
    refetchInterval: (data) => {
      const status = taskQ.data?.status;
      return ACTIVE_STATUSES.has(status) ? 4000 : false;
    },
    enabled: !!taskId,
  });

  // ── Cancel mutation ──
  const cancelMutation = useMutation({
    mutationFn: () => cancelTask(taskId),
    onSuccess: () => {
      setCancelConfirm(false);
      qc.invalidateQueries({ queryKey: ['task-status', taskId] });
      qc.invalidateQueries({ queryKey: ['agent-tasks'] });
    },
  });

  const task = taskQ.data;
  const runs = runsQ.data?.runs ?? [];
  const allMessages = runs.flatMap((r) => r.messages ?? []);
  const isActive = ACTIVE_STATUSES.has(task?.status);
  const agentMeta = AGENT_META[task?.agent_type ?? ''] ?? { icon: '🤖', label: task?.agent_type ?? 'Agent' };

  const TABS = [
    { key: 'timeline', label: 'Timeline',   icon: Clock },
    { key: 'tools',    label: 'Tool Calls', icon: Wrench },
    { key: 'handoffs', label: 'Handoffs',   icon: ArrowRight },
    { key: 'output',   label: 'Output',     icon: FileText },
    { key: 'memory',   label: 'Messages',   icon: MessageSquare },
  ];

  if (taskQ.isLoading) {
    return (
      <div className="flex items-center justify-center py-24 text-gray-500">
        <Loader2 className="w-6 h-6 animate-spin mr-2" /> Loading task…
      </div>
    );
  }

  if (taskQ.isError) {
    return (
      <div className="flex items-center gap-2 text-red-600 py-12 justify-center">
        <AlertCircle className="w-5 h-5" />
        Could not load task. It may have been deleted or you may not have access.
      </div>
    );
  }

  return (
    <div className="space-y-5 p-1">
      {/* Back */}
      <Button variant="ghost" size="sm" onClick={() => navigate('/agents')}>
        <ChevronLeft className="w-4 h-4 mr-1" /> Agent Control Center
      </Button>

      {/* Task Header */}
      <Card>
        <CardContent className="p-5">
          <div className="flex flex-col sm:flex-row sm:items-start sm:justify-between gap-3">
            <div className="flex items-start gap-3">
              <span className="text-3xl flex-shrink-0">{agentMeta.icon}</span>
              <div>
                <h1 className="text-lg font-bold text-gray-900">{task?.title ?? '(untitled task)'}</h1>
                {task?.description && (
                  <p className="text-sm text-gray-500 mt-0.5">{task.description}</p>
                )}
                <div className="flex items-center gap-3 mt-2">
                  <StatusBadge status={task?.status} large />
                  <span className="text-xs text-gray-400">{agentMeta.label}</span>
                  {task?.created_at && (
                    <span className="text-xs text-gray-400">
                      {formatDistanceToNow(new Date(task.created_at), { addSuffix: true })}
                    </span>
                  )}
                </div>
              </div>
            </div>

            {/* Actions */}
            <div className="flex items-center gap-2 flex-shrink-0">
              {isActive && (
                <>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => {
                      taskQ.refetch();
                      runsQ.refetch();
                    }}
                    aria-label="Refresh"
                  >
                    <RefreshCw className={`w-4 h-4 ${taskQ.isFetching ? 'animate-spin' : ''}`} />
                  </Button>
                  {!cancelConfirm ? (
                    <Button variant="danger" size="sm" onClick={() => setCancelConfirm(true)}>
                      <XCircle className="w-4 h-4 mr-1" /> Cancel
                    </Button>
                  ) : (
                    <div className="flex items-center gap-2">
                      <span className="text-sm text-red-600 font-medium">Confirm cancel?</span>
                      <Button
                        variant="danger"
                        size="sm"
                        isLoading={cancelMutation.isPending}
                        onClick={() => cancelMutation.mutate()}
                      >
                        Yes
                      </Button>
                      <Button variant="ghost" size="sm" onClick={() => setCancelConfirm(false)}>No</Button>
                    </div>
                  )}
                </>
              )}
              {task?.status === 'failed' && (
                <Button
                  size="sm"
                  variant="secondary"
                  onClick={() => navigate(`/agents/${task.agent_type}/run`)}
                >
                  <Play className="w-3.5 h-3.5 mr-1" /> Retry
                </Button>
              )}
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Agent handoff visualization */}
      {runs.length > 0 && (
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center gap-2 mb-3 text-sm font-medium text-gray-600">
              <Bot className="w-4 h-4" /> Agent Flow
            </div>
            <AgentHandoffTimeline runs={runs} />
          </CardContent>
        </Card>
      )}

      {/* Tabs */}
      <div>
        <div className="flex border-b border-gray-200 overflow-x-auto" role="tablist">
          {TABS.map(({ key, label, icon: Icon }) => (
            <button
              key={key}
              role="tab"
              aria-selected={activeTab === key}
              onClick={() => setActiveTab(key)}
              className={`flex items-center gap-1.5 px-4 py-2.5 text-sm font-medium whitespace-nowrap border-b-2 transition-colors ${
                activeTab === key
                  ? 'border-indigo-600 text-indigo-700'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              <Icon className="w-3.5 h-3.5" />
              {label}
              {key === 'tools' && allMessages.filter((m) => m.role === 'action').length > 0 && (
                <span className="ml-1 px-1.5 py-0.5 bg-indigo-100 text-indigo-700 text-xs rounded-full">
                  {allMessages.filter((m) => m.role === 'action').length}
                </span>
              )}
            </button>
          ))}
        </div>

        <div className="mt-4" role="tabpanel" aria-label={activeTab}>
          {/* Timeline */}
          {activeTab === 'timeline' && (
            <Card>
              <CardContent className="p-5">
                {allMessages.length === 0 ? (
                  <div className="text-center py-8 text-gray-400">
                    {isActive ? (
                      <div className="flex items-center justify-center gap-2">
                        <Loader2 className="w-5 h-5 animate-spin text-indigo-500" />
                        <span>Agent is working…</span>
                      </div>
                    ) : (
                      <span>No execution steps recorded.</span>
                    )}
                  </div>
                ) : (
                  <div className="relative pl-5 space-y-3">
                    <PlannerSteps messages={allMessages} />
                  </div>
                )}
              </CardContent>
            </Card>
          )}

          {/* Tool Calls */}
          {activeTab === 'tools' && (
            <Card>
              <CardContent className="p-5">
                <ToolCallsTable messages={allMessages} />
              </CardContent>
            </Card>
          )}

          {/* Handoffs */}
          {activeTab === 'handoffs' && (
            <Card>
              <CardContent className="p-5">
                {runs.length === 0 ? (
                  <p className="text-sm text-gray-400">No agent runs recorded yet.</p>
                ) : (
                  <div className="space-y-4">
                    {runs.map((run, i) => {
                      const aMeta = AGENT_META[run.agent_type] ?? { icon: '🤖', label: run.agent_type };
                      return (
                        <div key={run.run_id} className="flex gap-4 items-start">
                          <div className="flex flex-col items-center">
                            <div className="w-8 h-8 rounded-full bg-indigo-50 border border-indigo-200 flex items-center justify-center text-base">{aMeta.icon}</div>
                            {i < runs.length - 1 && <div className="w-0.5 h-6 bg-gray-200 mt-1" />}
                          </div>
                          <div>
                            <div className="font-medium text-sm text-gray-900">{aMeta.label}</div>
                            <div className="flex items-center gap-2 mt-0.5">
                              <StatusBadge status={run.status} />
                              {run.steps_taken > 0 && (
                                <span className="text-xs text-gray-400">{run.steps_taken} steps</span>
                              )}
                            </div>
                          </div>
                        </div>
                      );
                    })}
                  </div>
                )}
              </CardContent>
            </Card>
          )}

          {/* Output */}
          {activeTab === 'output' && (
            <FinalOutput
              result={task?.result}
              errorMessage={task?.error_message}
              status={task?.status}
            />
          )}

          {/* Messages (Memory) */}
          {activeTab === 'memory' && (
            <div className="space-y-2">
              {allMessages.length === 0 ? (
                <Card>
                  <CardContent className="py-10 text-center text-gray-400">
                    {isActive ? (
                      <div className="flex items-center justify-center gap-2">
                        <Loader2 className="w-5 h-5 animate-spin text-indigo-500" />
                        <span>Waiting for messages…</span>
                      </div>
                    ) : (
                      'No messages recorded.'
                    )}
                  </CardContent>
                </Card>
              ) : (
                allMessages.map((msg, i) => <MessageCard key={i} msg={msg} index={i} />)
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
