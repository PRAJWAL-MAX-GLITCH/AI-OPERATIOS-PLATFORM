/**
 * Agent Task Composer — /agents/:agentType/run
 * Allows users to compose and submit a task to a specific agent.
 */
import { useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useQuery, useMutation } from '@tanstack/react-query';
import {
  Bot, ChevronLeft, Play, Lightbulb, FolderOpen, Loader2,
} from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '../../components/ui/Card';
import { Button } from '../../components/ui/Button';
import { Input } from '../../components/ui/Input';
import { enqueueAgentTask, fetchProjects } from '../../services/agentApi';
import { AGENT_META, AGENT_COLORS, EXAMPLE_PROMPTS } from '../../services/agentConstants';

export default function AgentTaskComposer() {
  const { agentType } = useParams();
  const navigate = useNavigate();
  const meta   = AGENT_META[agentType] ?? { label: agentType, icon: '🤖', color: 'blue', description: '' };
  const colors = AGENT_COLORS[meta.color] ?? AGENT_COLORS.blue;
  const examples = EXAMPLE_PROMPTS[agentType] ?? [];

  const [title, setTitle]             = useState('');
  const [description, setDescription] = useState('');
  const [projectId, setProjectId]     = useState('');
  const [error, setError]             = useState('');

  // Load projects for the selector
  const projectsQ = useQuery({
    queryKey: ['projects-for-agent'],
    queryFn: fetchProjects,
    staleTime: 60_000,
  });
  const projects = Array.isArray(projectsQ.data) ? projectsQ.data : [];

  const submitMutation = useMutation({
    mutationFn: (payload) => enqueueAgentTask(payload),
    onSuccess: (data) => {
      navigate(`/agents/tasks/${data.task_id}`);
    },
    onError: (err) => {
      setError(err.response?.data?.detail ?? 'Failed to submit task. Please try again.');
    },
  });

  const handleSubmit = (e) => {
    e.preventDefault();
    setError('');
    if (!title.trim()) { setError('Task title is required.'); return; }
    submitMutation.mutate({
      agent_type: agentType,
      task_title: title.trim(),
      task_description: description.trim() || undefined,
      project_id: projectId || undefined,
    });
  };

  const applyExample = (prompt) => {
    setTitle(prompt);
    setDescription('');
  };

  return (
    <div className="space-y-6 max-w-2xl mx-auto p-1">
      {/* Back nav */}
      <Button variant="ghost" size="sm" onClick={() => navigate(`/agents/${agentType}`)} aria-label="Back">
        <ChevronLeft className="w-4 h-4 mr-1" /> {meta.label}
      </Button>

      {/* Header */}
      <div className="flex items-center gap-3">
        <div className={`text-3xl p-3 rounded-xl ${colors.bg}`}>{meta.icon}</div>
        <div>
          <h1 className="text-xl font-bold text-gray-900">New Task — {meta.label}</h1>
          <p className="text-sm text-gray-500">{meta.description}</p>
        </div>
      </div>

      {/* Example prompts */}
      {examples.length > 0 && (
        <Card className="border-dashed">
          <CardHeader>
            <CardTitle className="text-sm flex items-center gap-2">
              <Lightbulb className="w-4 h-4 text-amber-500" /> Example tasks (click to use)
            </CardTitle>
          </CardHeader>
          <CardContent className="pt-0 space-y-2">
            {examples.map((ex, i) => (
              <button
                key={i}
                type="button"
                onClick={() => applyExample(ex)}
                className="w-full text-left text-sm text-gray-600 hover:text-indigo-700 hover:bg-indigo-50 rounded-lg px-3 py-2 transition-colors border border-transparent hover:border-indigo-200"
              >
                "{ex}"
              </button>
            ))}
          </CardContent>
        </Card>
      )}

      {/* Composer form */}
      <Card>
        <CardContent className="p-6">
          <form onSubmit={handleSubmit} className="space-y-4" noValidate>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1" htmlFor="task-title">
                Task Objective <span className="text-red-500">*</span>
              </label>
              <Input
                id="task-title"
                placeholder={`e.g. ${examples[0] ?? 'Describe what you want the agent to do'}`}
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                required
                aria-required="true"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1" htmlFor="task-desc">
                Additional Context <span className="text-gray-400 font-normal">(optional)</span>
              </label>
              <textarea
                id="task-desc"
                rows={4}
                placeholder="Provide extra detail, constraints, or background information…"
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm text-gray-900 placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent resize-none"
              />
            </div>

            {/* Project selector */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1" htmlFor="project-select">
                <FolderOpen className="inline w-4 h-4 mr-1 text-gray-400" />
                Associate with Project <span className="text-gray-400 font-normal">(optional)</span>
              </label>
              <select
                id="project-select"
                value={projectId}
                onChange={(e) => setProjectId(e.target.value)}
                className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm text-gray-900 focus:outline-none focus:ring-2 focus:ring-indigo-500"
              >
                <option value="">— No project —</option>
                {projects.map((p) => (
                  <option key={p.id} value={p.id}>{p.name}</option>
                ))}
              </select>
            </div>

            {/* Error */}
            {error && (
              <div role="alert" className="rounded-md bg-red-50 border border-red-200 px-4 py-3 text-sm text-red-700">
                {error}
              </div>
            )}

            <div className="flex justify-end gap-3 pt-2 border-t">
              <Button type="button" variant="ghost" onClick={() => navigate(`/agents/${agentType}`)}>
                Cancel
              </Button>
              <Button type="submit" isLoading={submitMutation.isPending} aria-label="Submit task">
                <Play className="w-4 h-4 mr-2" />
                {submitMutation.isPending ? 'Submitting…' : 'Submit Task'}
              </Button>
            </div>
          </form>
        </CardContent>
      </Card>
    </div>
  );
}
