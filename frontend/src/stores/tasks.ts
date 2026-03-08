import { ref } from 'vue'
import { defineStore } from 'pinia'
import {
  fetchTasksByList,
  createTask as apiCreateTask,
  moveTask as apiMoveTask,
  reorderTasks as apiReorderTasks,
  syncTasks as apiSyncTasks,
  updateTaskStatus as apiUpdateTaskStatus,
  deleteTask as apiDeleteTask,
  type Task,
} from '@/api/tasks'

export const useTaskStore = defineStore('tasks', () => {
  const prioritized = ref<Task[]>([])
  const unprioritized = ref<Task[]>([])
  const completed = ref<Task[]>([])
  const loading = ref(false)
  const syncing = ref(false)
  const error = ref<string | null>(null)

  async function fetchTasks() {
    loading.value = true
    error.value = null
    try {
      const data = await fetchTasksByList()
      prioritized.value = data.prioritized
      unprioritized.value = data.unprioritized
      completed.value = data.completed
    } catch (e: unknown) {
      error.value = e instanceof Error ? e.message : 'Failed to load tasks'
    } finally {
      loading.value = false
    }
  }

  async function createTask(title: string, description?: string, priority?: number) {
    error.value = null
    try {
      const task = await apiCreateTask({ title, description, priority })
      unprioritized.value.push(task)
    } catch (e: unknown) {
      error.value = e instanceof Error ? e.message : 'Failed to create task'
    }
  }

  async function moveTaskToList(taskId: string, destination: string, position?: number) {
    error.value = null
    try {
      await apiMoveTask(taskId, destination, position)
      await fetchTasks()
    } catch (e: unknown) {
      error.value = e instanceof Error ? e.message : 'Failed to move task'
    }
  }

  async function reorder(listType: string, order: { id: string; position: number }[]) {
    error.value = null
    try {
      await apiReorderTasks(listType, order)
    } catch (e: unknown) {
      error.value = e instanceof Error ? e.message : 'Failed to reorder tasks'
    }
  }

  async function sync() {
    syncing.value = true
    error.value = null
    try {
      await apiSyncTasks()
      await fetchTasks()
    } catch (e: unknown) {
      error.value = e instanceof Error ? e.message : 'Sync failed'
    } finally {
      syncing.value = false
    }
  }

  async function updateStatus(taskId: string, status: string) {
    error.value = null
    try {
      await apiUpdateTaskStatus(taskId, status)
      await fetchTasks()
    } catch (e: unknown) {
      error.value = e instanceof Error ? e.message : 'Failed to update status'
    }
  }

  async function removeTask(taskId: string) {
    error.value = null
    try {
      await apiDeleteTask(taskId)
      prioritized.value = prioritized.value.filter((t) => t.id !== taskId)
      unprioritized.value = unprioritized.value.filter((t) => t.id !== taskId)
      completed.value = completed.value.filter((t) => t.id !== taskId)
    } catch (e: unknown) {
      error.value = e instanceof Error ? e.message : 'Failed to delete task'
    }
  }

  return {
    prioritized,
    unprioritized,
    completed,
    loading,
    syncing,
    error,
    fetchTasks,
    createTask,
    moveTaskToList,
    reorder,
    sync,
    updateStatus,
    removeTask,
  }
})
