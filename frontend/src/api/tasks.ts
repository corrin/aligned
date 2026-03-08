import api from '@/api/client'

export interface Task {
  id: string
  user_id: string
  task_user_email: string | null
  provider: string
  provider_task_id: string
  title: string
  description: string | null
  status: string
  due_date: string | null
  priority: number | null
  project_id: string | null
  project_name: string | null
  parent_id: string | null
  section_id: string | null
  list_type: string | null
  position: number | null
  content_hash: string
  last_synced: string | null
  created_at: string
  updated_at: string
}

export interface TasksByList {
  prioritized: Task[]
  unprioritized: Task[]
  completed: Task[]
}

export async function fetchTasksByList(): Promise<TasksByList> {
  const response = await api.get('/tasks/by-list')
  return response.data
}

export async function createTask(data: {
  title: string
  description?: string
  priority?: number
}): Promise<Task> {
  const response = await api.post('/tasks', data)
  return response.data
}

export async function updateTask(id: string, data: Partial<Task>): Promise<Task> {
  const response = await api.patch(`/tasks/${id}`, data)
  return response.data
}

export async function deleteTask(id: string): Promise<void> {
  await api.delete(`/tasks/${id}`)
}

export async function moveTask(
  taskId: string,
  destination: string,
  position?: number,
): Promise<void> {
  await api.post('/tasks/move', { task_id: taskId, destination, position })
}

export async function reorderTasks(
  listType: string,
  order: { id: string; position: number }[],
): Promise<void> {
  await api.post('/tasks/reorder', { list_type: listType, order })
}

export async function syncTasks(): Promise<{ status: string; message: string }> {
  const response = await api.post('/tasks/sync')
  return response.data
}

export async function updateTaskStatus(
  id: string,
  status: string,
): Promise<void> {
  await api.post(`/tasks/${id}/update-status`, { status })
}
