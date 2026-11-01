"use client";

import {
  AlertCircle,
  AlertTriangle,
  Calendar,
  CheckCircle2,
  Clock,
  Filter,
  Link as LinkIcon,
  Loader2,
  Plus,
  RefreshCw,
  Search,
  Sparkles,
  Trash2,
  X,
} from "lucide-react";
import * as React from "react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { apiFetch } from "@/lib/api/client";
import { getApiErrorMessage } from "@/lib/api/errors";
import type {
  EventDto,
  FunctionDto,
  TaskDto,
  TaskPriority,
  TaskStatus,
  TimelineProposalDto,
  TimelineSummaryDto,
} from "@/types/api";

interface TimelineWorkspaceProps {
  event: EventDto;
  initialTasks: TaskDto[];
  initialSummary: TimelineSummaryDto | null;
  functions?: FunctionDto[];
}

export function TimelineWorkspace({
  event,
  initialTasks,
  initialSummary,
  functions = [],
}: TimelineWorkspaceProps) {
  const [tasks, setTasks] = React.useState<TaskDto[]>(initialTasks);
  const [summary, setSummary] = React.useState<TimelineSummaryDto | null>(initialSummary);
  const [viewMode, setViewMode] = React.useState<"kanban" | "milestone">("kanban");

  // Filtering
  const [searchQuery, setSearchQuery] = React.useState("");
  const [statusFilter, setStatusFilter] = React.useState<string>("all");
  const [priorityFilter, setPriorityFilter] = React.useState<string>("all");

  // Task Create/Edit Modal
  const [taskModalOpen, setTaskModalOpen] = React.useState(false);
  const [editingTaskId, setEditingTaskId] = React.useState<string | null>(null);
  const [taskTitle, setTaskTitle] = React.useState("");
  const [taskDesc, setTaskDesc] = React.useState("");
  const [taskDueAt, setTaskDueAt] = React.useState("");
  const [taskPriority, setTaskPriority] = React.useState<TaskPriority>("medium");
  const [taskStatus, setTaskStatus] = React.useState<TaskStatus>("todo");
  const [taskFunctionId, setTaskFunctionId] = React.useState<string>("");
  const [savingTask, setSavingTask] = React.useState(false);

  // Dependency Management Modal
  const [depModalOpen, setDepModalOpen] = React.useState(false);
  const [selectedTaskForDeps, setSelectedTaskForDeps] = React.useState<TaskDto | null>(null);
  const [newPrereqId, setNewPrereqId] = React.useState("");
  const [savingDep, setSavingDep] = React.useState(false);

  // AI Assistant Modal
  const [aiModalOpen, setAiModalOpen] = React.useState(false);
  const [aiPrompt, setAiPrompt] = React.useState("");
  const [aiGenerating, setAiGenerating] = React.useState(false);
  const [aiProposal, setAiProposal] = React.useState<TimelineProposalDto | null>(null);
  const [selectedTaskRefs, setSelectedTaskRefs] = React.useState<Set<string>>(new Set());
  const [aiAccepting, setAiAccepting] = React.useState(false);

  const [error, setError] = React.useState<string | null>(null);
  const [successMsg, setSuccessMsg] = React.useState<string | null>(null);

  const refreshSummaryAndTasks = async () => {
    try {
      const [sumRes, tasksRes] = await Promise.all([
        apiFetch<TimelineSummaryDto>(`/api/v1/events/${event.id}/tasks/summary`),
        apiFetch<TaskDto[]>(`/api/v1/events/${event.id}/tasks`),
      ]);
      setSummary(sumRes.data);
      setTasks(tasksRes.data);
    } catch (err) {
      setError(getApiErrorMessage(err));
    }
  };

  const handleOpenCreateTask = () => {
    setEditingTaskId(null);
    setTaskTitle("");
    setTaskDesc("");
    setTaskDueAt("");
    setTaskPriority("medium");
    setTaskStatus("todo");
    setTaskFunctionId("");
    setError(null);
    setTaskModalOpen(true);
  };

  const handleOpenEditTask = (task: TaskDto) => {
    setEditingTaskId(task.id);
    setTaskTitle(task.title);
    setTaskDesc(task.description || "");
    setTaskDueAt(task.due_at ? task.due_at.substring(0, 16) : "");
    setTaskPriority(task.priority);
    setTaskStatus(task.status);
    setTaskFunctionId(task.function_id || "");
    setError(null);
    setTaskModalOpen(true);
  };

  const handleSaveTask = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!taskTitle.trim()) {
      setError("Task title is required");
      return;
    }
    setSavingTask(true);
    setError(null);
    try {
      const payload = {
        title: taskTitle.trim(),
        description: taskDesc.trim() || null,
        due_at: taskDueAt ? new Date(taskDueAt).toISOString() : null,
        priority: taskPriority,
        function_id: taskFunctionId || null,
      };

      if (editingTaskId) {
        await apiFetch<TaskDto>(`/api/v1/events/${event.id}/tasks/${editingTaskId}`, {
          method: "PATCH",
          json: { ...payload, status: taskStatus },
        });
        setSuccessMsg("Task updated successfully");
      } else {
        await apiFetch<TaskDto>(`/api/v1/events/${event.id}/tasks`, {
          method: "POST",
          json: payload,
        });
        setSuccessMsg("Task created successfully");
      }
      setTaskModalOpen(false);
      await refreshSummaryAndTasks();
    } catch (err) {
      setError(getApiErrorMessage(err));
    } finally {
      setSavingTask(false);
    }
  };

  const handleStatusChange = async (taskId: string, newStatus: TaskStatus) => {
    try {
      await apiFetch<TaskDto>(`/api/v1/events/${event.id}/tasks/${taskId}`, {
        method: "PATCH",
        json: { status: newStatus },
      });
      await refreshSummaryAndTasks();
    } catch (err) {
      setError(getApiErrorMessage(err));
    }
  };

  const handleDeleteTask = async (taskId: string) => {
    if (!window.confirm("Are you sure you want to delete this task?")) return;
    try {
      await apiFetch<void>(`/api/v1/events/${event.id}/tasks/${taskId}`, {
        method: "DELETE",
      });
      setSuccessMsg("Task deleted");
      await refreshSummaryAndTasks();
    } catch (err) {
      setError(getApiErrorMessage(err));
    }
  };

  // Manage Dependencies
  const handleOpenDeps = (task: TaskDto) => {
    setSelectedTaskForDeps(task);
    setNewPrereqId("");
    setError(null);
    setDepModalOpen(true);
  };

  const handleAddDependency = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedTaskForDeps || !newPrereqId) return;
    setSavingDep(true);
    setError(null);
    try {
      await apiFetch<void>(`/api/v1/events/${event.id}/tasks/${selectedTaskForDeps.id}/dependencies`, {
        method: "POST",
        json: { depends_on_task_id: newPrereqId },
      });
      setSuccessMsg("Prerequisite dependency added");
      setNewPrereqId("");
      await refreshSummaryAndTasks();
      const updated = (await apiFetch<TaskDto[]>(`/api/v1/events/${event.id}/tasks`)).data.find(
        (t) => t.id === selectedTaskForDeps.id
      );
      if (updated) setSelectedTaskForDeps(updated);
    } catch (err) {
      setError(getApiErrorMessage(err));
    } finally {
      setSavingDep(false);
    }
  };

  const handleRemoveDependency = async (prereqId: string) => {
    if (!selectedTaskForDeps) return;
    setSavingDep(true);
    setError(null);
    try {
      await apiFetch<void>(
        `/api/v1/events/${event.id}/tasks/${selectedTaskForDeps.id}/dependencies/${prereqId}`,
        {
          method: "DELETE",
        }
      );
      setSuccessMsg("Dependency removed");
      await refreshSummaryAndTasks();
      const updated = (await apiFetch<TaskDto[]>(`/api/v1/events/${event.id}/tasks`)).data.find(
        (t) => t.id === selectedTaskForDeps.id
      );
      if (updated) setSelectedTaskForDeps(updated);
    } catch (err) {
      setError(getApiErrorMessage(err));
    } finally {
      setSavingDep(false);
    }
  };

  // AI Timeline Generation
  const handleGenerateTimeline = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!aiPrompt.trim()) return;
    setAiGenerating(true);
    setError(null);
    try {
      const proposal = await apiFetch<TimelineProposalDto>(
        `/api/v1/events/${event.id}/tasks/ai/generate`,
        {
          method: "POST",
          json: { prompt: aiPrompt.trim() },
        }
      );
      setAiProposal(proposal.data);
      const allRefs = new Set<string>(proposal.data.payload.proposed_tasks.map((t) => t.client_ref));
      setSelectedTaskRefs(allRefs);
    } catch (err) {
      setError(getApiErrorMessage(err));
    } finally {
      setAiGenerating(false);
    }
  };

  const toggleSelectTaskRef = (clientRef: string) => {
    setSelectedTaskRefs((prev) => {
      const next = new Set(prev);
      if (next.has(clientRef)) next.delete(clientRef);
      else next.add(clientRef);
      return next;
    });
  };

  const handleAcceptTimelineProposal = async () => {
    if (!aiProposal) return;
    setAiAccepting(true);
    setError(null);
    try {
      await apiFetch<TimelineProposalDto>(
        `/api/v1/events/${event.id}/tasks/ai/proposals/${aiProposal.id}/accept`,
        {
          method: "POST",
          json: {
            base_revision: aiProposal.base_revision,
            accepted_task_refs: Array.from(selectedTaskRefs),
          },
        }
      );
      setSuccessMsg(`Successfully imported ${selectedTaskRefs.size} tasks to the schedule!`);
      setAiModalOpen(false);
      setAiProposal(null);
      setAiPrompt("");
      await refreshSummaryAndTasks();
    } catch (err) {
      setError(getApiErrorMessage(err));
    } finally {
      setAiAccepting(false);
    }
  };

  // Filtering tasks
  const filteredTasks = tasks.filter((t) => {
    if (searchQuery.trim()) {
      const q = searchQuery.toLowerCase();
      const match =
        t.title.toLowerCase().includes(q) ||
        (t.description && t.description.toLowerCase().includes(q));
      if (!match) return false;
    }
    if (statusFilter !== "all" && t.status !== statusFilter) return false;
    if (priorityFilter !== "all" && t.priority !== priorityFilter) return false;
    return true;
  });

  const getPriorityBadgeVariant = (priority: TaskPriority): "default" | "secondary" | "outline" | "warning" => {
    switch (priority) {
      case "urgent":
        return "warning";
      case "high":
        return "default";
      case "medium":
        return "secondary";
      case "low":
        return "outline";
    }
  };

  const getStatusBadgeVariant = (status: TaskStatus): "default" | "secondary" | "outline" | "success" | "warning" | "muted" => {
    switch (status) {
      case "done":
        return "success";
      case "in_progress":
        return "default";
      case "blocked":
        return "warning";
      case "cancelled":
        return "muted";
      default:
        return "outline";
    }
  };

  const kanbanColumns: TaskStatus[] = ["todo", "in_progress", "blocked", "done"];

  return (
    <div className="space-y-6">
      {/* Notifications */}
      {error && (
        <div className="rounded-lg border border-destructive/50 bg-destructive/10 p-4 text-destructive flex items-start justify-between">
          <div className="flex items-center gap-2">
            <AlertCircle className="h-5 w-5 shrink-0" />
            <span className="text-sm font-medium">{error}</span>
          </div>
          <button onClick={() => setError(null)} className="text-destructive hover:opacity-75">
            <X className="h-4 w-4" />
          </button>
        </div>
      )}

      {successMsg && (
        <div className="rounded-lg border border-emerald-500/50 bg-emerald-500/10 p-4 text-emerald-700 dark:text-emerald-400 flex items-start justify-between">
          <div className="flex items-center gap-2">
            <CheckCircle2 className="h-5 w-5 shrink-0" />
            <span className="text-sm font-medium">{successMsg}</span>
          </div>
          <button onClick={() => setSuccessMsg(null)} className="hover:opacity-75">
            <X className="h-4 w-4" />
          </button>
        </div>
      )}

      {/* Timeline Metrics Overview */}
      <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-7 gap-4">
        <Card className="p-4">
          <div className="text-xs text-muted-foreground font-medium uppercase">Total Tasks</div>
          <div className="text-2xl font-bold mt-1">{summary?.total_tasks ?? tasks.length}</div>
        </Card>
        <Card className="p-4">
          <div className="text-xs text-muted-foreground font-medium uppercase">Completed</div>
          <div className="text-2xl font-bold mt-1 text-emerald-600">
            {summary?.completed_tasks ?? 0}
          </div>
          <div className="text-xs text-muted-foreground mt-0.5">
            {summary ? Math.round(summary.completion_percentage) : 0}% done
          </div>
        </Card>
        <Card className="p-4">
          <div className="text-xs text-muted-foreground font-medium uppercase">In Progress</div>
          <div className="text-2xl font-bold mt-1 text-blue-600">
            {summary?.in_progress_tasks ?? 0}
          </div>
        </Card>
        <Card className="p-4">
          <div className="text-xs text-muted-foreground font-medium uppercase">Pending (Todo)</div>
          <div className="text-2xl font-bold mt-1">{summary?.pending_tasks ?? 0}</div>
        </Card>
        <Card className="p-4">
          <div className="text-xs text-muted-foreground font-medium uppercase">Blocked</div>
          <div className="text-2xl font-bold mt-1 text-red-600">
            {summary?.blocked_tasks ?? 0}
          </div>
        </Card>
        <Card className="p-4">
          <div className="text-xs text-muted-foreground font-medium uppercase">Overdue</div>
          <div className="text-2xl font-bold mt-1 text-amber-600">
            {summary?.overdue_tasks ?? 0}
          </div>
        </Card>
        <Card className="p-4">
          <div className="text-xs text-muted-foreground font-medium uppercase">Upcoming 7d</div>
          <div className="text-2xl font-bold mt-1 text-indigo-600">
            {summary?.upcoming_tasks ?? 0}
          </div>
        </Card>
      </div>

      {/* Action Header & View Switcher */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 border-b pb-4">
        <div className="flex items-center gap-2">
          <div className="inline-flex rounded-md border p-1 bg-muted/40">
            <button
              onClick={() => setViewMode("kanban")}
              className={`px-3 py-1.5 text-xs font-medium rounded transition-all ${
                viewMode === "kanban"
                  ? "bg-background text-foreground shadow-sm"
                  : "text-muted-foreground hover:text-foreground"
              }`}
            >
              Kanban Board
            </button>
            <button
              onClick={() => setViewMode("milestone")}
              className={`px-3 py-1.5 text-xs font-medium rounded transition-all ${
                viewMode === "milestone"
                  ? "bg-background text-foreground shadow-sm"
                  : "text-muted-foreground hover:text-foreground"
              }`}
            >
              Milestone Schedule
            </button>
          </div>

          <Button variant="outline" size="sm" onClick={refreshSummaryAndTasks}>
            <RefreshCw className="h-3.5 w-3.5 mr-1" />
            Refresh
          </Button>
        </div>

        <div className="flex items-center gap-2 w-full sm:w-auto">
          <Button
            variant="outline"
            className="border-primary/50 text-primary hover:bg-primary/10 gap-1.5"
            onClick={() => setAiModalOpen(true)}
          >
            <Sparkles className="h-4 w-4 text-primary" />
            TimelineAI Schedule Assistant
          </Button>
          <Button onClick={handleOpenCreateTask} className="gap-1">
            <Plus className="h-4 w-4" />
            New Task
          </Button>
        </div>
      </div>

      {/* Filter and Search Bar */}
      <div className="flex flex-wrap items-center gap-3">
        <div className="relative flex-1 min-w-[200px]">
          <Search className="absolute left-3 top-2.5 h-4 w-4 text-muted-foreground" />
          <Input
            placeholder="Search tasks by title or description..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="pl-9"
          />
        </div>

        <div className="flex items-center gap-2">
          <Filter className="h-4 w-4 text-muted-foreground" />
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="h-9 rounded-md border bg-background px-3 py-1 text-sm shadow-sm"
          >
            <option value="all">All Statuses</option>
            <option value="todo">To Do</option>
            <option value="in_progress">In Progress</option>
            <option value="blocked">Blocked</option>
            <option value="done">Completed</option>
            <option value="cancelled">Cancelled</option>
          </select>

          <select
            value={priorityFilter}
            onChange={(e) => setPriorityFilter(e.target.value)}
            className="h-9 rounded-md border bg-background px-3 py-1 text-sm shadow-sm"
          >
            <option value="all">All Priorities</option>
            <option value="urgent">Urgent</option>
            <option value="high">High</option>
            <option value="medium">Medium</option>
            <option value="low">Low</option>
          </select>
        </div>
      </div>

      {/* Kanban Board View */}
      {viewMode === "kanban" && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {kanbanColumns.map((colStatus) => {
            const colTasks = filteredTasks.filter((t) => t.status === colStatus);
            return (
              <div key={colStatus} className="flex flex-col rounded-lg bg-muted/30 border p-3 min-h-[500px]">
                <div className="flex items-center justify-between mb-3 px-1">
                  <div className="flex items-center gap-2">
                    <span className="font-semibold text-sm capitalize">
                      {colStatus === "in_progress"
                        ? "In Progress"
                        : colStatus === "todo"
                        ? "To Do"
                        : colStatus}
                    </span>
                    <Badge variant="secondary" className="text-xs">
                      {colTasks.length}
                    </Badge>
                  </div>
                </div>

                <div className="flex-1 space-y-3 overflow-y-auto pr-1">
                  {colTasks.map((task) => (
                    <Card key={task.id} className="shadow-sm hover:shadow transition-shadow">
                      <CardContent className="p-3.5 space-y-2.5">
                        <div className="flex items-start justify-between gap-2">
                          <h4 className="font-medium text-sm leading-tight">{task.title}</h4>
                          <Badge variant={getPriorityBadgeVariant(task.priority)} className="text-[10px] shrink-0 uppercase">
                            {task.priority}
                          </Badge>
                        </div>

                        {task.description && (
                          <p className="text-xs text-muted-foreground line-clamp-2">
                            {task.description}
                          </p>
                        )}

                        {task.due_at && (
                          <div className="flex items-center gap-1.5 text-xs text-muted-foreground">
                            <Clock className="h-3 w-3" />
                            <span>{new Date(task.due_at).toLocaleDateString()}</span>
                          </div>
                        )}

                        {task.depends_on_task_ids.length > 0 && (
                          <div className="flex items-center gap-1.5 text-xs text-amber-600 dark:text-amber-400">
                            <LinkIcon className="h-3 w-3" />
                            <span>{task.depends_on_task_ids.length} Prerequisite(s)</span>
                          </div>
                        )}

                        <div className="flex items-center justify-between pt-2 border-t mt-2">
                          <select
                            value={task.status}
                            onChange={(e) => handleStatusChange(task.id, e.target.value as TaskStatus)}
                            className="text-xs h-7 rounded border bg-background px-1.5 text-muted-foreground"
                          >
                            <option value="todo">To Do</option>
                            <option value="in_progress">In Progress</option>
                            <option value="blocked">Blocked</option>
                            <option value="done">Done</option>
                            <option value="cancelled">Cancelled</option>
                          </select>

                          <div className="flex items-center gap-1">
                            <Button
                              variant="ghost"
                              size="sm"
                              className="h-7 w-7 p-0"
                              title="Manage dependencies"
                              onClick={() => handleOpenDeps(task)}
                            >
                              <LinkIcon className="h-3.5 w-3.5 text-muted-foreground" />
                            </Button>
                            <Button
                              variant="ghost"
                              size="sm"
                              className="h-7 px-2 text-xs"
                              onClick={() => handleOpenEditTask(task)}
                            >
                              Edit
                            </Button>
                            <Button
                              variant="ghost"
                              size="sm"
                              className="h-7 w-7 p-0 text-destructive"
                              onClick={() => handleDeleteTask(task.id)}
                            >
                              <Trash2 className="h-3.5 w-3.5" />
                            </Button>
                          </div>
                        </div>
                      </CardContent>
                    </Card>
                  ))}

                  {colTasks.length === 0 && (
                    <div className="h-24 flex items-center justify-center border-2 border-dashed rounded text-xs text-muted-foreground">
                      No tasks in this column
                    </div>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* Milestone Chronological View */}
      {viewMode === "milestone" && (
        <Card>
          <CardHeader>
            <CardTitle>Milestone Timeline</CardTitle>
            <CardDescription>
              Chronological schedule of tasks, sorted by target completion date with dependency markers.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {filteredTasks
                .slice()
                .sort((a, b) => {
                  if (!a.due_at) return 1;
                  if (!b.due_at) return -1;
                  return new Date(a.due_at).getTime() - new Date(b.due_at).getTime();
                })
                .map((task, idx) => {
                  const prereqs = tasks.filter((t) =>
                    task.depends_on_task_ids.includes(t.id)
                  );
                  return (
                    <div
                      key={task.id}
                      className="flex items-start gap-4 p-4 rounded-lg border hover:bg-muted/10 transition-colors"
                    >
                      <div className="flex flex-col items-center">
                        <div
                          className={`w-8 h-8 rounded-full flex items-center justify-center font-bold text-xs ${
                            task.status === "done"
                              ? "bg-emerald-500 text-white"
                              : task.status === "in_progress"
                              ? "bg-blue-500 text-white"
                              : task.status === "blocked"
                              ? "bg-red-500 text-white"
                              : "bg-muted text-muted-foreground border"
                          }`}
                        >
                          {idx + 1}
                        </div>
                        {idx < filteredTasks.length - 1 && (
                          <div className="w-0.5 h-12 bg-border my-1" />
                        )}
                      </div>

                      <div className="flex-1 space-y-1">
                        <div className="flex items-center justify-between">
                          <h4 className="font-semibold text-base">{task.title}</h4>
                          <div className="flex items-center gap-2">
                            <Badge variant={getStatusBadgeVariant(task.status)}>
                              {task.status}
                            </Badge>
                            <Badge variant={getPriorityBadgeVariant(task.priority)}>
                              {task.priority}
                            </Badge>
                          </div>
                        </div>

                        {task.description && (
                          <p className="text-sm text-muted-foreground">{task.description}</p>
                        )}

                        <div className="flex flex-wrap items-center gap-4 text-xs text-muted-foreground pt-1">
                          <span className="flex items-center gap-1 font-medium">
                            <Calendar className="h-3.5 w-3.5" />
                            {task.due_at
                              ? new Date(task.due_at).toLocaleString()
                              : "Unscheduled"}
                          </span>

                          {task.origin === "ai_accepted" && (
                            <Badge variant="outline" className="text-[10px]">
                              PlanAI Generated
                            </Badge>
                          )}

                          {prereqs.length > 0 && (
                            <div className="flex items-center gap-1 text-amber-600 dark:text-amber-400">
                              <LinkIcon className="h-3 w-3" />
                              <span>Prerequisites: {prereqs.map((p) => p.title).join(", ")}</span>
                            </div>
                          )}
                        </div>
                      </div>

                      <div className="flex items-center gap-1">
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => handleOpenDeps(task)}
                        >
                          Dependencies
                        </Button>
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => handleOpenEditTask(task)}
                        >
                          Edit
                        </Button>
                      </div>
                    </div>
                  );
                })}

              {filteredTasks.length === 0 && (
                <div className="py-12 text-center text-muted-foreground">
                  No tasks matching the selected filters.
                </div>
              )}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Task Create/Edit Modal */}
      {taskModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
          <Card className="w-full max-w-lg shadow-xl">
            <CardHeader className="flex flex-row items-center justify-between">
              <div>
                <CardTitle>{editingTaskId ? "Edit Task" : "New Task"}</CardTitle>
                <CardDescription>
                  {editingTaskId
                    ? "Update task details, schedule, or status"
                    : "Create a new planning action item"}
                </CardDescription>
              </div>
              <button
                onClick={() => setTaskModalOpen(false)}
                className="text-muted-foreground hover:text-foreground"
              >
                <X className="h-5 w-5" />
              </button>
            </CardHeader>
            <form onSubmit={handleSaveTask}>
              <CardContent className="space-y-4">
                <div className="space-y-1">
                  <label className="text-sm font-medium">Task Title *</label>
                  <Input
                    required
                    value={taskTitle}
                    onChange={(e) => setTaskTitle(e.target.value)}
                    placeholder="e.g. Confirm wedding venue deposit"
                  />
                </div>

                <div className="space-y-1">
                  <label className="text-sm font-medium">Description</label>
                  <textarea
                    rows={3}
                    value={taskDesc}
                    onChange={(e) => setTaskDesc(e.target.value)}
                    placeholder="Add specific instructions, notes, or vendor details..."
                    className="w-full rounded-md border bg-background px-3 py-2 text-sm shadow-sm"
                  />
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-1">
                    <label className="text-sm font-medium">Due Date & Time</label>
                    <Input
                      type="datetime-local"
                      value={taskDueAt}
                      onChange={(e) => setTaskDueAt(e.target.value)}
                    />
                  </div>

                  <div className="space-y-1">
                    <label className="text-sm font-medium">Priority</label>
                    <select
                      value={taskPriority}
                      onChange={(e) => setTaskPriority(e.target.value as TaskPriority)}
                      className="w-full h-9 rounded-md border bg-background px-3 text-sm shadow-sm"
                    >
                      <option value="low">Low</option>
                      <option value="medium">Medium</option>
                      <option value="high">High</option>
                      <option value="urgent">Urgent</option>
                    </select>
                  </div>
                </div>

                {editingTaskId && (
                  <div className="space-y-1">
                    <label className="text-sm font-medium">Status</label>
                    <select
                      value={taskStatus}
                      onChange={(e) => setTaskStatus(e.target.value as TaskStatus)}
                      className="w-full h-9 rounded-md border bg-background px-3 text-sm shadow-sm"
                    >
                      <option value="todo">To Do</option>
                      <option value="in_progress">In Progress</option>
                      <option value="blocked">Blocked</option>
                      <option value="done">Completed</option>
                      <option value="cancelled">Cancelled</option>
                    </select>
                  </div>
                )}

                {functions.length > 0 && (
                  <div className="space-y-1">
                    <label className="text-sm font-medium">Linked Function / Ceremony</label>
                    <select
                      value={taskFunctionId}
                      onChange={(e) => setTaskFunctionId(e.target.value)}
                      className="w-full h-9 rounded-md border bg-background px-3 text-sm shadow-sm"
                    >
                      <option value="">None (General event task)</option>
                      {functions.map((fn) => (
                        <option key={fn.id} value={fn.id}>
                          {fn.name} {fn.location_name ? `(${fn.location_name})` : ""}
                        </option>
                      ))}
                    </select>
                  </div>
                )}
              </CardContent>

              <CardFooter className="flex justify-end gap-2 border-t pt-4">
                <Button
                  type="button"
                  variant="outline"
                  onClick={() => setTaskModalOpen(false)}
                >
                  Cancel
                </Button>
                <Button type="submit" disabled={savingTask}>
                  {savingTask && <Loader2 className="h-4 w-4 mr-1 animate-spin" />}
                  {editingTaskId ? "Save Changes" : "Create Task"}
                </Button>
              </CardFooter>
            </form>
          </Card>
        </div>
      )}

      {/* Manage Dependencies Modal */}
      {depModalOpen && selectedTaskForDeps && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
          <Card className="w-full max-w-lg shadow-xl">
            <CardHeader className="flex flex-row items-center justify-between">
              <div>
                <CardTitle>Manage Task Dependencies</CardTitle>
                <CardDescription>
                  Prerequisites that must be completed before &quot;{selectedTaskForDeps.title}&quot; can proceed.
                </CardDescription>
              </div>
              <button
                onClick={() => setDepModalOpen(false)}
                className="text-muted-foreground hover:text-foreground"
              >
                <X className="h-5 w-5" />
              </button>
            </CardHeader>
            <CardContent className="space-y-4">
              {/* Existing dependencies */}
              <div className="space-y-2">
                <h4 className="text-sm font-medium">Current Prerequisites</h4>
                {selectedTaskForDeps.depends_on_task_ids.length === 0 ? (
                  <p className="text-xs text-muted-foreground">
                    This task has no prerequisites. It can be started at any time.
                  </p>
                ) : (
                  <div className="space-y-2">
                    {selectedTaskForDeps.depends_on_task_ids.map((prereqId) => {
                      const prereq = tasks.find((t) => t.id === prereqId);
                      return (
                        <div
                          key={prereqId}
                          className="flex items-center justify-between rounded border p-2 text-sm"
                        >
                          <div>
                            <div className="font-medium">{prereq?.title || prereqId}</div>
                            <div className="text-xs text-muted-foreground">
                              Status: {prereq?.status || "unknown"}
                            </div>
                          </div>
                          <Button
                            variant="ghost"
                            size="sm"
                            className="text-destructive h-8 px-2"
                            onClick={() => handleRemoveDependency(prereqId)}
                            disabled={savingDep}
                          >
                            Remove
                          </Button>
                        </div>
                      );
                    })}
                  </div>
                )}
              </div>

              {/* Add new dependency form */}
              <form onSubmit={handleAddDependency} className="space-y-2 pt-2 border-t">
                <h4 className="text-sm font-medium">Add Prerequisite Task</h4>
                <p className="text-xs text-muted-foreground">
                  The dependency will be checked for circular cycles (DAG) and due-date chronological sequence.
                </p>
                <div className="flex gap-2">
                  <select
                    value={newPrereqId}
                    onChange={(e) => setNewPrereqId(e.target.value)}
                    className="flex-1 h-9 rounded-md border bg-background px-3 text-sm shadow-sm"
                    required
                  >
                    <option value="">Select a prerequisite task...</option>
                    {tasks
                      .filter(
                        (t) =>
                          t.id !== selectedTaskForDeps.id &&
                          !selectedTaskForDeps.depends_on_task_ids.includes(t.id)
                      )
                      .map((t) => (
                        <option key={t.id} value={t.id}>
                          {t.title} ({t.status})
                        </option>
                      ))}
                  </select>
                  <Button type="submit" disabled={!newPrereqId || savingDep}>
                    {savingDep && <Loader2 className="h-4 w-4 mr-1 animate-spin" />}
                    Add
                  </Button>
                </div>
              </form>
            </CardContent>
            <CardFooter className="flex justify-end border-t pt-4">
              <Button onClick={() => setDepModalOpen(false)}>Done</Button>
            </CardFooter>
          </Card>
        </div>
      )}

      {/* AI Assistant Modal */}
      {aiModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
          <Card className="w-full max-w-2xl max-h-[90vh] flex flex-col shadow-xl">
            <CardHeader className="flex flex-row items-center justify-between">
              <div>
                <CardTitle className="flex items-center gap-2">
                  <Sparkles className="h-5 w-5 text-primary" />
                  TimelineAI Schedule Assistant
                </CardTitle>
                <CardDescription>
                  Generate ceremony milestones, preparation schedules, and task dependencies with Gemini AI.
                </CardDescription>
              </div>
              <button
                onClick={() => {
                  setAiModalOpen(false);
                  setAiProposal(null);
                }}
                className="text-muted-foreground hover:text-foreground"
              >
                <X className="h-5 w-5" />
              </button>
            </CardHeader>

            <div className="flex-1 overflow-y-auto p-6 space-y-4">
              {!aiProposal ? (
                <form onSubmit={handleGenerateTimeline} className="space-y-4">
                  <div className="space-y-2">
                    <label className="text-sm font-medium">Planning Goal / Instructions</label>
                    <textarea
                      rows={4}
                      required
                      value={aiPrompt}
                      onChange={(e) => setAiPrompt(e.target.value)}
                      placeholder="e.g. Generate a complete 6-month planning timeline for a 3-day Indian wedding with Sangeet, Mehendi, and Reception. Include vendor deadlines and payment reminders."
                      className="w-full rounded-md border bg-background px-3 py-2 text-sm shadow-sm"
                    />
                  </div>
                  <Button
                    type="submit"
                    disabled={aiGenerating || !aiPrompt.trim()}
                    className="w-full gap-2"
                  >
                    {aiGenerating ? (
                      <>
                        <Loader2 className="h-4 w-4 animate-spin" />
                        Generating Schedule via Gemini...
                      </>
                    ) : (
                      <>
                        <Sparkles className="h-4 w-4" />
                        Generate Recommended Timeline
                      </>
                    )}
                  </Button>
                </form>
              ) : (
                <div className="space-y-4">
                  {aiProposal.payload.summary && (
                    <div className="rounded-lg border bg-primary/5 p-3 text-sm">
                      <p className="font-medium text-foreground">{aiProposal.payload.summary}</p>
                    </div>
                  )}

                  {aiProposal.payload.assumptions.length > 0 && (
                    <div className="rounded-lg border bg-muted/40 p-3 text-xs space-y-1">
                      <span className="font-semibold text-muted-foreground uppercase">
                        AI Assumptions:
                      </span>
                      <ul className="list-disc list-inside space-y-0.5">
                        {aiProposal.payload.assumptions.map((asm: string, i: number) => (
                          <li key={i}>{asm}</li>
                        ))}
                      </ul>
                    </div>
                  )}

                  {aiProposal.payload.warnings.length > 0 && (
                    <div className="rounded-lg border border-amber-500/40 bg-amber-500/10 p-3 text-xs text-amber-800 dark:text-amber-300 space-y-1">
                      <div className="flex items-center gap-1 font-semibold">
                        <AlertTriangle className="h-3.5 w-3.5" />
                        Warnings & Considerations:
                      </div>
                      <ul className="list-disc list-inside space-y-0.5">
                        {aiProposal.payload.warnings.map((warn: string, i: number) => (
                          <li key={i}>{warn}</li>
                        ))}
                      </ul>
                    </div>
                  )}

                  <div className="space-y-2">
                    <div className="flex items-center justify-between">
                      <h4 className="text-sm font-semibold">
                        Recommended Tasks ({aiProposal.payload.proposed_tasks.length})
                      </h4>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => {
                          if (selectedTaskRefs.size === aiProposal.payload.proposed_tasks.length) {
                            setSelectedTaskRefs(new Set());
                          } else {
                            setSelectedTaskRefs(
                              new Set(aiProposal.payload.proposed_tasks.map((t) => t.client_ref))
                            );
                          }
                        }}
                        className="text-xs h-7"
                      >
                        {selectedTaskRefs.size === aiProposal.payload.proposed_tasks.length
                          ? "Deselect All"
                          : "Select All"}
                      </Button>
                    </div>

                    <div className="space-y-2 max-h-[300px] overflow-y-auto pr-1">
                      {aiProposal.payload.proposed_tasks.map((taskItem) => (
                        <div
                          key={taskItem.client_ref}
                          onClick={() => toggleSelectTaskRef(taskItem.client_ref)}
                          className={`flex items-start gap-3 p-3 rounded-lg border cursor-pointer transition-colors ${
                            selectedTaskRefs.has(taskItem.client_ref)
                              ? "border-primary bg-primary/5"
                              : "border-border opacity-70"
                          }`}
                        >
                          <input
                            type="checkbox"
                            checked={selectedTaskRefs.has(taskItem.client_ref)}
                            onChange={() => toggleSelectTaskRef(taskItem.client_ref)}
                            className="mt-1"
                          />
                          <div className="flex-1 space-y-1">
                            <div className="flex items-center justify-between">
                              <span className="font-medium text-sm">{taskItem.title}</span>
                              <Badge variant={getPriorityBadgeVariant(taskItem.priority)}>
                                {taskItem.priority}
                              </Badge>
                            </div>
                            {taskItem.description && (
                              <p className="text-xs text-muted-foreground">{taskItem.description}</p>
                            )}
                            {taskItem.depends_on.length > 0 && (
                              <div className="text-[11px] text-amber-600 dark:text-amber-400">
                                Prereq refs: {taskItem.depends_on.join(", ")}
                              </div>
                            )}
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              )}
            </div>

            <CardFooter className="flex justify-between border-t pt-4">
              {aiProposal ? (
                <>
                  <Button
                    variant="outline"
                    onClick={() => setAiProposal(null)}
                    disabled={aiAccepting}
                  >
                    Back to Prompt
                  </Button>
                  <Button
                    onClick={handleAcceptTimelineProposal}
                    disabled={selectedTaskRefs.size === 0 || aiAccepting}
                    className="gap-2"
                  >
                    {aiAccepting ? (
                      <>
                        <Loader2 className="h-4 w-4 animate-spin" />
                        Importing Tasks...
                      </>
                    ) : (
                      <>
                        <CheckCircle2 className="h-4 w-4" />
                        Accept & Import Selected ({selectedTaskRefs.size})
                      </>
                    )}
                  </Button>
                </>
              ) : (
                <Button
                  variant="outline"
                  onClick={() => setAiModalOpen(false)}
                  className="ml-auto"
                >
                  Close
                </Button>
              )}
            </CardFooter>
          </Card>
        </div>
      )}
    </div>
  );
}
