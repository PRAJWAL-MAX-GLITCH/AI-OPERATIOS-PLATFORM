/**
 * Agent Control Center — API service layer
 * All calls go through the shared axios instance from services/api.js
 */
import api from './api';

// ─── Agent Registry ───────────────────────────────────────────────────────────

/** Returns { agents: string[] } */
export const fetchAvailableAgents = () =>
  api.get('/agents').then((r) => r.data.data);

// ─── Task Submission ──────────────────────────────────────────────────────────

/**
 * Run an agent synchronously (blocks until done / times out).
 * @param {{ agent_type, task_title, task_description, project_id }} payload
 */
export const runAgentSync = (payload) =>
  api.post('/agents/run', payload).then((r) => r.data.data);

/**
 * Enqueue an agent task for background Celery execution.
 * Returns immediately with task_id.
 */
export const enqueueAgentTask = (payload) =>
  api.post('/agents/task', payload).then((r) => r.data.data);

// ─── Task Status & History ────────────────────────────────────────────────────

/** Poll a single task's status */
export const fetchTaskStatus = (taskId) =>
  api.get(`/agents/tasks/${taskId}`).then((r) => r.data.data);

/** Full message history for a task */
export const fetchTaskHistory = (taskId) =>
  api.get(`/agents/history/${taskId}`).then((r) => r.data.data);

/** All run records + messages for a task */
export const fetchTaskRuns = (taskId) =>
  api.get(`/agents/tasks/${taskId}/runs`).then((r) => r.data.data);

/** Paginated list of user's agent tasks */
export const fetchUserTasks = (params = {}) =>
  api.get('/agents/tasks', { params }).then((r) => r.data.data);

/** Cancel a pending/running task */
export const cancelTask = (taskId) =>
  api.post(`/agents/tasks/${taskId}/cancel`).then((r) => r.data.data);

// ─── Projects (for task composer selects) ────────────────────────────────────

export const fetchProjects = () =>
  api.get('/projects').then((r) => r.data.data?.projects ?? r.data.data ?? []);
