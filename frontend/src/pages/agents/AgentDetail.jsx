/**
 * Agent Detail Page — /agents/:agentType
 * Shows capabilities, tool list, configuration, and run history for a specific agent.
 */
import { useParams, useNavigate } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import {
  Bot, Play, ChevronLeft, Wrench, Zap, Clock,
  CheckCircle2, XCircle, ChevronRight, Loader2, AlertCircle,
} from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '../../components/ui/Card';
import { Button } from '../../components/ui/Button';
import { fetchUserTasks } from '../../services/agentApi';
import { AGENT_META, AGENT_COLORS, STATUS_META } from '../../services/agentConstants';
import { formatDistanceToNow } from 'date-fns';

function StatusBadge({ status }) {
  const meta = STATUS_META[status] ?? STATUS_META.pending;
  return (
    <span className={`inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-medium ${meta.color}`}>
      <span className={`w-1.5 h-1.5 rounded-full ${meta.dot}`} />
      {meta.label}
    </span>
  );
}

export default function AgentDetail() {
  const { agentType } = useParams();
  const navigate = useNavigate();
  const meta   = AGENT_META[agentType] ?? { label: agentType, description: '', icon: '🤖', color: 'blue', capabilities: [], tools: [] };
  const colors = AGENT_COLORS[meta.color] ?? AGENT_COLORS.blue;

  // Fetch tasks for this specific agent type
  const tasksQ = useQuery({
    queryKey: ['agent-tasks', agentType],
    queryFn: () => fetchUserTasks({ agent_type: agentType, limit: 50 }),
    refetchInterval: 5000,
  });

  const tasks     = tasksQ.data?.tasks ?? [];
  const completed = tasks.filter((t) => t.status === 'completed').length;
  const failed    = tasks.filter((t) => t.status === 'failed').length;
  const successRate = tasks.length > 0
    ? Math.round((completed / tasks.length) * 100)
    : null;

  return (
    <div className="space-y-6 p-1">
      {/* Header */}
      <div className="flex items-center gap-3">
        <Button variant="ghost" size="sm" onClick={() => navigate('/agents')} aria-label="Back to agents">
          <ChevronLeft className="w-4 h-4 mr-1" /> Agents
        </Button>
      </div>

      {/* Hero card */}
      <Card className={`border-2 ${colors.border}`}>
        <CardContent className="p-6 flex flex-col sm:flex-row sm:items-center gap-5">
          <div className={`text-5xl p-4 rounded-2xl ${colors.bg} flex-shrink-0 w-fit`}>{meta.icon}</div>
          <div className="flex-1">
            <h1 className="text-2xl font-bold text-gray-900">{meta.label}</h1>
            <p className="text-gray-500 mt-1">{meta.description}</p>
            <div className="flex flex-wrap gap-2 mt-3">
              {meta.capabilities.map((cap) => (
                <span key={cap} className={`px-2.5 py-1 rounded-full text-xs font-medium ${colors.bg} ${colors.text}`}>
                  {cap}
                </span>
              ))}
            </div>
          </div>
          <Button
            className="flex-shrink-0"
            onClick={() => navigate(`/agents/${agentType}/run`)}
            aria-label={`Run ${meta.label}`}
          >
            <Play className="w-4 h-4 mr-2" /> Run Task
          </Button>
        </CardContent>
      </Card>

      {/* Stats + Tools */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {/* Stats */}
        <Card>
          <CardHeader><CardTitle className="text-sm">Performance</CardTitle></CardHeader>
          <CardContent className="space-y-3 pt-0">
            <div className="flex justify-between text-sm">
              <span className="text-gray-500">Total Runs</span>
              <span className="font-semibold">{tasks.length}</span>
            </div>
            <div className="flex justify-between text-sm">
              <span className="text-gray-500 flex items-center gap-1"><CheckCircle2 className="w-3.5 h-3.5 text-green-500" /> Completed</span>
              <span className="font-semibold text-green-700">{completed}</span>
            </div>
            <div className="flex justify-between text-sm">
              <span className="text-gray-500 flex items-center gap-1"><XCircle className="w-3.5 h-3.5 text-red-500" /> Failed</span>
              <span className="font-semibold text-red-700">{failed}</span>
            </div>
            {successRate !== null && (
              <div className="flex justify-between text-sm border-t pt-2">
                <span className="text-gray-500">Success Rate</span>
                <span className={`font-bold ${successRate >= 75 ? 'text-green-600' : 'text-red-600'}`}>
                  {successRate}%
                </span>
              </div>
            )}
          </CardContent>
        </Card>

        {/* Tools */}
        <Card className="md:col-span-2">
          <CardHeader><CardTitle className="text-sm flex items-center gap-2"><Wrench className="w-4 h-4" /> Available Tools</CardTitle></CardHeader>
          <CardContent className="pt-0">
            {meta.tools.length === 0 ? (
              <p className="text-sm text-gray-400">This agent uses no external tools (pure LLM reasoning).</p>
            ) : (
              <div className="flex flex-wrap gap-2">
                {meta.tools.map((tool) => (
                  <span key={tool} className="inline-flex items-center gap-1 px-3 py-1.5 bg-gray-100 text-gray-700 text-sm rounded-lg font-mono border border-gray-200">
                    <Zap className="w-3.5 h-3.5 text-indigo-500" /> {tool}
                  </span>
                ))}
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Execution History */}
      <section>
        <h2 className="text-lg font-semibold text-gray-800 mb-3 flex items-center gap-2">
          <Clock className="w-5 h-5 text-gray-400" /> Execution History
        </h2>
        <Card>
          {tasksQ.isLoading ? (
            <CardContent className="py-10 text-center text-gray-400">
              <Loader2 className="w-5 h-5 animate-spin mx-auto mb-2" /> Loading…
            </CardContent>
          ) : tasks.length === 0 ? (
            <CardContent className="py-10 text-center text-gray-400">
              <Bot className="w-10 h-10 mx-auto mb-2 opacity-30" />
              No runs yet for this agent.
            </CardContent>
          ) : (
            <div className="divide-y divide-gray-100">
              {tasks.map((task) => (
                <div
                  key={task.task_id}
                  className="flex items-center justify-between px-5 py-3 hover:bg-gray-50 cursor-pointer group"
                  onClick={() => navigate(`/agents/tasks/${task.task_id}`)}
                  role="button"
                  tabIndex={0}
                  onKeyDown={(e) => e.key === 'Enter' && navigate(`/agents/tasks/${task.task_id}`)}
                  aria-label={`View task: ${task.title}`}
                >
                  <div className="min-w-0 flex-1">
                    <p className="font-medium text-gray-900 text-sm truncate">{task.title || '(untitled)'}</p>
                    {task.description && (
                      <p className="text-xs text-gray-400 truncate">{task.description}</p>
                    )}
                  </div>
                  <div className="flex items-center gap-4 flex-shrink-0">
                    <StatusBadge status={task.status} />
                    {task.created_at && (
                      <span className="text-xs text-gray-400 hidden sm:block">
                        {formatDistanceToNow(new Date(task.created_at), { addSuffix: true })}
                      </span>
                    )}
                    <ChevronRight className="w-4 h-4 text-gray-300 group-hover:text-indigo-500 transition-colors" />
                  </div>
                </div>
              ))}
            </div>
          )}
        </Card>
      </section>
    </div>
  );
}
