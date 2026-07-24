/**
 * Agent Run History — /agents/history
 * Full searchable, filterable, paginated table of all agent task runs.
 */
import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import {
  History, Search, Filter, ChevronRight, Loader2,
  Bot, Clock, RefreshCw,
} from 'lucide-react';
import { Card, CardContent } from '../../components/ui/Card';
import { Button } from '../../components/ui/Button';
import { Input } from '../../components/ui/Input';
import { fetchUserTasks } from '../../services/agentApi';
import { AGENT_META, STATUS_META } from '../../services/agentConstants';
import { formatDistanceToNow, format } from 'date-fns';

function StatusBadge({ status }) {
  const meta = STATUS_META[status] ?? STATUS_META.pending;
  return (
    <span className={`inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-medium ${meta.color}`}>
      <span className={`w-1.5 h-1.5 rounded-full ${meta.dot}`} />
      {meta.label}
    </span>
  );
}

const PAGE_SIZE = 20;

export default function AgentHistory() {
  const navigate = useNavigate();
  const [search, setSearch]         = useState('');
  const [statusFilter, setStatus]   = useState('all');
  const [agentFilter, setAgent]     = useState('all');
  const [page, setPage]             = useState(0);

  const tasksQ = useQuery({
    queryKey: ['agent-tasks-history', statusFilter, agentFilter, page],
    queryFn: () =>
      fetchUserTasks({
        status: statusFilter === 'all' ? undefined : statusFilter,
        agent_type: agentFilter === 'all' ? undefined : agentFilter,
        limit: PAGE_SIZE,
        offset: page * PAGE_SIZE,
      }),
    staleTime: 10_000,
    refetchInterval: 10_000,
  });

  const allTasks = tasksQ.data?.tasks ?? [];
  const total    = tasksQ.data?.total ?? 0;

  // Client-side search on title
  const tasks = search.trim()
    ? allTasks.filter((t) =>
        (t.title ?? '').toLowerCase().includes(search.toLowerCase()) ||
        (t.description ?? '').toLowerCase().includes(search.toLowerCase())
      )
    : allTasks;

  const agentTypes = Object.keys(AGENT_META);
  const totalPages = Math.max(1, Math.ceil(total / PAGE_SIZE));

  return (
    <div className="space-y-6 p-1">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 flex items-center gap-2">
            <History className="w-6 h-6 text-indigo-600" /> Run History
          </h1>
          <p className="text-gray-500 mt-1 text-sm">
            Browse, filter, and inspect all agent task runs.
          </p>
        </div>
        <Button variant="ghost" size="sm" onClick={() => tasksQ.refetch()} aria-label="Refresh">
          <RefreshCw className={`w-4 h-4 mr-1 ${tasksQ.isFetching ? 'animate-spin' : ''}`} />
          Refresh
        </Button>
      </div>

      {/* Filters */}
      <div className="flex flex-col sm:flex-row gap-3">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
          <Input
            className="pl-9"
            placeholder="Search by task title or description…"
            value={search}
            onChange={(e) => { setSearch(e.target.value); setPage(0); }}
            aria-label="Search tasks"
          />
        </div>

        <div className="flex items-center gap-2">
          <Filter className="w-4 h-4 text-gray-400 flex-shrink-0" />
          <select
            value={agentFilter}
            onChange={(e) => { setAgent(e.target.value); setPage(0); }}
            className="text-sm border border-gray-300 rounded-md px-2 py-2 text-gray-700 focus:outline-none focus:ring-2 focus:ring-indigo-500"
            aria-label="Filter by agent type"
          >
            <option value="all">All Agents</option>
            {agentTypes.map((t) => (
              <option key={t} value={t}>{AGENT_META[t].label}</option>
            ))}
          </select>

          <select
            value={statusFilter}
            onChange={(e) => { setStatus(e.target.value); setPage(0); }}
            className="text-sm border border-gray-300 rounded-md px-2 py-2 text-gray-700 focus:outline-none focus:ring-2 focus:ring-indigo-500"
            aria-label="Filter by status"
          >
            <option value="all">All Statuses</option>
            {Object.entries(STATUS_META).map(([k, v]) => (
              <option key={k} value={k}>{v.label}</option>
            ))}
          </select>
        </div>
      </div>

      {/* Table */}
      <Card>
        {tasksQ.isLoading ? (
          <CardContent className="py-14 text-center text-gray-400">
            <Loader2 className="w-6 h-6 animate-spin mx-auto mb-2" />
            Loading history…
          </CardContent>
        ) : tasks.length === 0 ? (
          <CardContent className="py-14 text-center">
            <Bot className="w-10 h-10 text-gray-300 mx-auto mb-3" />
            <p className="text-gray-500 font-medium">No tasks found</p>
            <p className="text-gray-400 text-sm mt-1">Try adjusting your filters.</p>
          </CardContent>
        ) : (
          <>
            {/* Desktop table */}
            <div className="hidden md:block overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-gray-100 text-left">
                    <th className="px-5 py-3 text-xs font-medium text-gray-500 uppercase tracking-wide">Task</th>
                    <th className="px-5 py-3 text-xs font-medium text-gray-500 uppercase tracking-wide">Agent</th>
                    <th className="px-5 py-3 text-xs font-medium text-gray-500 uppercase tracking-wide">Status</th>
                    <th className="px-5 py-3 text-xs font-medium text-gray-500 uppercase tracking-wide">Created</th>
                    <th className="px-5 py-3 text-xs font-medium text-gray-500 uppercase tracking-wide w-10"></th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-50">
                  {tasks.map((task) => {
                    const meta = AGENT_META[task.agent_type] ?? { icon: '🤖', label: task.agent_type };
                    return (
                      <tr
                        key={task.task_id}
                        className="hover:bg-gray-50 cursor-pointer group transition-colors"
                        onClick={() => navigate(`/agents/tasks/${task.task_id}`)}
                        role="button"
                        tabIndex={0}
                        onKeyDown={(e) => e.key === 'Enter' && navigate(`/agents/tasks/${task.task_id}`)}
                        aria-label={`View task: ${task.title}`}
                      >
                        <td className="px-5 py-3">
                          <div className="font-medium text-gray-900 truncate max-w-xs">{task.title || '(untitled)'}</div>
                          {task.description && (
                            <div className="text-xs text-gray-400 truncate max-w-xs mt-0.5">{task.description}</div>
                          )}
                        </td>
                        <td className="px-5 py-3">
                          <div className="flex items-center gap-2">
                            <span>{meta.icon}</span>
                            <span className="text-gray-700">{meta.label}</span>
                          </div>
                        </td>
                        <td className="px-5 py-3"><StatusBadge status={task.status} /></td>
                        <td className="px-5 py-3 text-gray-400 text-xs">
                          {task.created_at ? (
                            <span title={format(new Date(task.created_at), 'PPpp')}>
                              {formatDistanceToNow(new Date(task.created_at), { addSuffix: true })}
                            </span>
                          ) : '—'}
                        </td>
                        <td className="px-5 py-3">
                          <ChevronRight className="w-4 h-4 text-gray-300 group-hover:text-indigo-500 transition-colors" />
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>

            {/* Mobile list */}
            <div className="md:hidden divide-y divide-gray-100">
              {tasks.map((task) => {
                const meta = AGENT_META[task.agent_type] ?? { icon: '🤖', label: task.agent_type };
                return (
                  <div
                    key={task.task_id}
                    className="flex items-center justify-between px-4 py-3 hover:bg-gray-50 cursor-pointer"
                    onClick={() => navigate(`/agents/tasks/${task.task_id}`)}
                    role="button"
                    tabIndex={0}
                    onKeyDown={(e) => e.key === 'Enter' && navigate(`/agents/tasks/${task.task_id}`)}
                    aria-label={`View task: ${task.title}`}
                  >
                    <div className="flex items-center gap-2 min-w-0">
                      <span>{meta.icon}</span>
                      <div className="min-w-0">
                        <p className="text-sm font-medium text-gray-900 truncate">{task.title || '(untitled)'}</p>
                        <StatusBadge status={task.status} />
                      </div>
                    </div>
                    <ChevronRight className="w-4 h-4 text-gray-300 flex-shrink-0" />
                  </div>
                );
              })}
            </div>
          </>
        )}
      </Card>

      {/* Pagination */}
      {totalPages > 1 && (
        <div className="flex items-center justify-between text-sm text-gray-500">
          <span>
            Showing {page * PAGE_SIZE + 1}–{Math.min((page + 1) * PAGE_SIZE, total)} of {total}
          </span>
          <div className="flex gap-2">
            <Button
              variant="secondary"
              size="sm"
              disabled={page === 0}
              onClick={() => setPage((p) => p - 1)}
              aria-label="Previous page"
            >
              Previous
            </Button>
            <Button
              variant="secondary"
              size="sm"
              disabled={page >= totalPages - 1}
              onClick={() => setPage((p) => p + 1)}
              aria-label="Next page"
            >
              Next
            </Button>
          </div>
        </div>
      )}
    </div>
  );
}
