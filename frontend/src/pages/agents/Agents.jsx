/**
 * Enterprise AI Agent Control Center
 * ====================================
 * Main landing page: shows all registered agents from backend,
 * recent task history, and quick-launch buttons.
 */
import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import {
  Bot, Play, History, ChevronRight, Zap, Clock,
  CheckCircle2, XCircle, AlertCircle, Loader2, RefreshCw,
} from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '../../components/ui/Card';
import { Button } from '../../components/ui/Button';
import { Badge } from '../../components/ui/Badge';
import { fetchAvailableAgents, fetchUserTasks } from '../../services/agentApi';
import { AGENT_META, AGENT_COLORS, STATUS_META } from '../../services/agentConstants';
import { formatDistanceToNow } from 'date-fns';

// ── Derived helpers ────────────────────────────────────────────────────────────

function agentMeta(type) {
  return AGENT_META[type] ?? {
    label: type,
    description: 'Custom agent.',
    icon: '🤖',
    color: 'blue',
    capabilities: [],
    tools: [],
  };
}

function StatusBadge({ status }) {
  const meta = STATUS_META[status] ?? STATUS_META.pending;
  return (
    <span className={`inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-medium ${meta.color}`}>
      <span className={`w-1.5 h-1.5 rounded-full ${meta.dot}`} />
      {meta.label}
    </span>
  );
}

function StatCard({ icon: Icon, label, value, color = 'text-gray-700' }) {
  return (
    <Card>
      <CardContent className="p-4 flex items-center gap-4">
        <div className="p-3 rounded-xl bg-gray-50">
          <Icon className={`w-5 h-5 ${color}`} />
        </div>
        <div>
          <div className="text-2xl font-bold text-gray-900">{value}</div>
          <div className="text-xs text-gray-500">{label}</div>
        </div>
      </CardContent>
    </Card>
  );
}

// ── Main Component ─────────────────────────────────────────────────────────────

export default function Agents() {
  const navigate = useNavigate();
  const [selectedFilter, setSelectedFilter] = useState('all');

  // Load registered agent types from backend
  const agentsQ = useQuery({
    queryKey: ['agents-registry'],
    queryFn: fetchAvailableAgents,
    staleTime: 60_000,
  });

  // Load recent tasks (last 20)
  const tasksQ = useQuery({
    queryKey: ['agent-tasks', selectedFilter],
    queryFn: () =>
      fetchUserTasks({
        status: selectedFilter === 'all' ? undefined : selectedFilter,
        limit: 20,
      }),
    refetchInterval: 5000, // poll for live status updates
  });

  const registeredTypes = agentsQ.data?.agents ?? [];
  const tasks = tasksQ.data?.tasks ?? [];

  // Derived analytics from real tasks
  const total     = tasks.length;
  const completed = tasks.filter((t) => t.status === 'completed').length;
  const failed    = tasks.filter((t) => t.status === 'failed').length;
  const active    = tasks.filter((t) => ['pending', 'running'].includes(t.status)).length;

  const STATUS_FILTERS = ['all', 'pending', 'running', 'completed', 'failed', 'cancelled'];

  return (
    <div className="space-y-8 p-1">
      {/* ── Header ── */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-gray-900 flex items-center gap-2">
            <Bot className="w-7 h-7 text-indigo-600" />
            Agent Control Center
          </h1>
          <p className="text-gray-500 mt-1">
            Discover, configure, and orchestrate autonomous AI agents.
          </p>
        </div>
      </div>

      {/* ── Stats Row ── */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard icon={Zap}          label="Total Tasks"      value={total}     color="text-indigo-600" />
        <StatCard icon={CheckCircle2} label="Completed"        value={completed} color="text-green-600"  />
        <StatCard icon={XCircle}      label="Failed"           value={failed}    color="text-red-600"    />
        <StatCard icon={Loader2}      label="Active"           value={active}    color="text-blue-600"   />
      </div>

      {/* ── Available Agents ── */}
      <section>
        <h2 className="text-lg font-semibold text-gray-800 mb-4">Available Agents</h2>
        {agentsQ.isLoading ? (
          <div className="flex items-center gap-2 text-gray-500 py-8 justify-center">
            <Loader2 className="w-5 h-5 animate-spin" /> Loading agents…
          </div>
        ) : agentsQ.isError ? (
          <div className="text-red-600 py-4 flex items-center gap-2">
            <AlertCircle className="w-5 h-5" />
            Could not load agent registry. Is the backend running?
          </div>
        ) : registeredTypes.length === 0 ? (
          <div className="text-gray-400 py-4">No agents registered yet.</div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-5">
            {registeredTypes.map((type) => {
              const meta   = agentMeta(type);
              const colors = AGENT_COLORS[meta.color] ?? AGENT_COLORS.blue;
              return (
                <Card
                  key={type}
                  className={`border ${colors.border} hover:shadow-md transition-all cursor-pointer group`}
                  onClick={() => navigate(`/agents/${type}`)}
                >
                  <CardContent className="p-5">
                    <div className="flex items-start justify-between mb-3">
                      <div className={`text-3xl p-2 rounded-xl ${colors.bg}`}>{meta.icon}</div>
                      <ChevronRight className="w-4 h-4 text-gray-400 group-hover:text-indigo-500 transition-colors mt-1" />
                    </div>
                    <h3 className={`font-semibold text-gray-900 mb-1`}>{meta.label}</h3>
                    <p className="text-xs text-gray-500 mb-3 line-clamp-2">{meta.description}</p>

                    {meta.tools.length > 0 && (
                      <div className="flex flex-wrap gap-1 mb-3">
                        {meta.tools.map((t) => (
                          <span key={t} className="px-2 py-0.5 bg-gray-100 text-gray-600 text-xs rounded-full font-mono">
                            {t}
                          </span>
                        ))}
                      </div>
                    )}

                    <Button
                      size="sm"
                      className="w-full mt-2"
                      onClick={(e) => { e.stopPropagation(); navigate(`/agents/${type}/run`); }}
                    >
                      <Play className="w-3.5 h-3.5 mr-1.5" /> Run Task
                    </Button>
                  </CardContent>
                </Card>
              );
            })}
          </div>
        )}
      </section>

      {/* ── Recent Task History ── */}
      <section>
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-semibold text-gray-800 flex items-center gap-2">
            <History className="w-5 h-5 text-gray-500" /> Recent Runs
          </h2>
          <div className="flex items-center gap-2">
            <select
              value={selectedFilter}
              onChange={(e) => setSelectedFilter(e.target.value)}
              className="text-sm border border-gray-200 rounded-md px-2 py-1 text-gray-600 focus:outline-none focus:ring-2 focus:ring-indigo-500"
              aria-label="Filter by status"
            >
              {STATUS_FILTERS.map((f) => (
                <option key={f} value={f}>{f === 'all' ? 'All Statuses' : STATUS_META[f]?.label ?? f}</option>
              ))}
            </select>
            <Button
              variant="ghost"
              size="sm"
              onClick={() => tasksQ.refetch()}
              aria-label="Refresh task list"
            >
              <RefreshCw className={`w-4 h-4 ${tasksQ.isFetching ? 'animate-spin' : ''}`} />
            </Button>
          </div>
        </div>

        <Card>
          {tasksQ.isLoading ? (
            <CardContent className="py-12 text-center text-gray-500">
              <Loader2 className="w-6 h-6 animate-spin mx-auto mb-2" />
              Loading task history…
            </CardContent>
          ) : tasks.length === 0 ? (
            <CardContent className="py-12 text-center">
              <Bot className="w-10 h-10 text-gray-300 mx-auto mb-3" />
              <p className="text-gray-500">No tasks yet. Run an agent to get started.</p>
            </CardContent>
          ) : (
            <div className="divide-y divide-gray-100">
              {tasks.map((task) => {
                const meta = agentMeta(task.agent_type);
                return (
                  <div
                    key={task.task_id}
                    className="flex items-center justify-between px-5 py-3 hover:bg-gray-50 cursor-pointer transition-colors group"
                    onClick={() => navigate(`/agents/tasks/${task.task_id}`)}
                    role="button"
                    tabIndex={0}
                    onKeyDown={(e) => e.key === 'Enter' && navigate(`/agents/tasks/${task.task_id}`)}
                    aria-label={`View task: ${task.title}`}
                  >
                    <div className="flex items-center gap-3 min-w-0">
                      <span className="text-xl flex-shrink-0">{meta.icon}</span>
                      <div className="min-w-0">
                        <p className="font-medium text-gray-900 text-sm truncate">{task.title || '(untitled)'}</p>
                        <p className="text-xs text-gray-400">{meta.label}</p>
                      </div>
                    </div>
                    <div className="flex items-center gap-4 flex-shrink-0">
                      <StatusBadge status={task.status} />
                      {task.created_at && (
                        <span className="text-xs text-gray-400 hidden sm:block whitespace-nowrap">
                          <Clock className="w-3 h-3 inline mr-1" />
                          {formatDistanceToNow(new Date(task.created_at), { addSuffix: true })}
                        </span>
                      )}
                      <ChevronRight className="w-4 h-4 text-gray-300 group-hover:text-indigo-500 transition-colors" />
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </Card>
      </section>
    </div>
  );
}
