"use client";

import {
  AlertCircle,
  AlertTriangle,
  Calendar,
  Check,
  CheckSquare,
  HelpCircle,
  History,
  Info,
  ListTodo,
  Loader2,
  MessageSquare,
  Plus,
  Sparkles,
  Square,
} from "lucide-react";
import * as React from "react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { apiFetch } from "@/lib/api/client";
import { getApiErrorMessage } from "@/lib/api/errors";
import type {
  ConversationDetailDto,
  ConversationDto,
  EventDto,
  PlanAcceptResponseDto,
  PlanProposalDto,
} from "@/types/api";

interface PlanAiWorkspaceProps {
  event: EventDto;
  initialConversations: ConversationDto[];
}

export function PlanAiWorkspace({ event, initialConversations }: PlanAiWorkspaceProps) {
  const [conversations, setConversations] = React.useState<ConversationDto[]>(initialConversations);
  const [activeConversationId, setActiveConversationId] = React.useState<string | null>(
    initialConversations[0]?.id || null,
  );
  const [activeConversation, setActiveConversation] = React.useState<ConversationDetailDto | null>(null);
  const [loadingConversation, setLoadingConversation] = React.useState(false);

  const [currentProposal, setCurrentProposal] = React.useState<PlanProposalDto | null>(null);
  const justGeneratedProposalRef = React.useRef<string | null>(null);
  const [selectedFunctionRefs, setSelectedFunctionRefs] = React.useState<Set<string>>(new Set());
  const [selectedTaskRefs, setSelectedTaskRefs] = React.useState<Set<string>>(new Set());

  const [userPrompt, setUserPrompt] = React.useState("");
  const [generating, setGenerating] = React.useState(false);
  const [accepting, setAccepting] = React.useState(false);
  const [rejecting, setRejecting] = React.useState(false);

  const [error, setError] = React.useState<string | null>(null);
  const [acceptanceSuccess, setAcceptanceSuccess] = React.useState<PlanAcceptResponseDto | null>(null);
  const [currentRevision, setCurrentRevision] = React.useState(event.revision);

  const isReadOnly = event.status === "archived" || event.my_role === "viewer";

  // Load conversation details when active conversation changes
  React.useEffect(() => {
    if (!activeConversationId) {
      setActiveConversation(null);
      setCurrentProposal(null);
      return;
    }

    let isMounted = true;
    setLoadingConversation(true);
    setError(null);

    if (justGeneratedProposalRef.current) {
      justGeneratedProposalRef.current = null;
      const call = apiFetch<ConversationDetailDto>(`/events/${event.id}/ai/conversations/${activeConversationId}`);
      if (call && typeof call.then === "function") {
        call
          .then(({ data }) => {
            if (isMounted && data) setActiveConversation(data);
          })
          .catch(() => {})
          .finally(() => {
            if (isMounted) setLoadingConversation(false);
          });
      } else {
        setLoadingConversation(false);
      }
      return;
    }

    const call = apiFetch<ConversationDetailDto>(`/events/${event.id}/ai/conversations/${activeConversationId}`);
    if (call && typeof call.then === "function") {
      call
        .then(async ({ data }) => {
          if (!isMounted || !data) return;
          setActiveConversation(data);

          // Find latest proposal in this conversation if any
          const messages = data.messages || [];
          const proposalMsg = [...messages].reverse().find((m) => m.proposal_id);
          if (proposalMsg?.proposal_id) {
            try {
              const res = await apiFetch<PlanProposalDto>(
                `/events/${event.id}/ai/proposals/${proposalMsg.proposal_id}`,
              );
              if (isMounted && res?.data) {
                setCurrentProposal(res.data);
                setSelectedFunctionRefs(
                  new Set(res.data.payload.proposed_functions.map((f) => f.client_ref)),
                );
                setSelectedTaskRefs(
                  new Set(res.data.payload.proposed_tasks.map((t) => t.client_ref)),
                );
              }
            } catch {
              // Proposal might not be available or expired
            }
          } else if (!currentProposal || currentProposal.conversation_id !== activeConversationId) {
            setCurrentProposal(null);
          }
        })
        .catch((err) => {
          if (isMounted) setError(getApiErrorMessage(err, "Failed to load conversation"));
        })
        .finally(() => {
          if (isMounted) setLoadingConversation(false);
        });
    } else {
      setLoadingConversation(false);
    }

    return () => {
      isMounted = false;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [activeConversationId, event.id]);

  const handleStartNewConversation = () => {
    setActiveConversationId(null);
    setActiveConversation(null);
    setCurrentProposal(null);
    setError(null);
    setAcceptanceSuccess(null);
  };

  const handleGeneratePlan = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!userPrompt.trim() || generating || isReadOnly) return;

    setGenerating(true);
    setError(null);
    setAcceptanceSuccess(null);

    try {
      const payload = {
        request: userPrompt.trim(),
        base_revision: currentRevision,
        conversation_id: activeConversationId,
      };

      const { data: proposal } = await apiFetch<PlanProposalDto>(
        `/events/${event.id}/plans/generate`,
        {
          method: "POST",
          json: payload,
        },
      );

      justGeneratedProposalRef.current = proposal.proposal_id;
      setCurrentProposal(proposal);
      setSelectedFunctionRefs(
        new Set(proposal.payload.proposed_functions.map((f) => f.client_ref)),
      );
      setSelectedTaskRefs(
        new Set(proposal.payload.proposed_tasks.map((t) => t.client_ref)),
      );

      // If this proposal created a new conversation or belongs to one, update list and select it
      if (proposal.conversation_id) {
        setActiveConversationId(proposal.conversation_id);
        // Refresh conversations list
        const { data: convList } = await apiFetch<{ items: ConversationDto[] }>(
          `/events/${event.id}/ai/conversations`,
        );
        setConversations(convList.items);
      }

      setUserPrompt("");
    } catch (err) {
      setError(getApiErrorMessage(err, "Failed to generate plan. Please try again."));
    } finally {
      setGenerating(false);
    }
  };

  const toggleFunctionSelection = (ref: string) => {
    setSelectedFunctionRefs((prev) => {
      const next = new Set(prev);
      if (next.has(ref)) next.delete(ref);
      else next.add(ref);
      return next;
    });
  };

  const toggleTaskSelection = (ref: string) => {
    setSelectedTaskRefs((prev) => {
      const next = new Set(prev);
      if (next.has(ref)) next.delete(ref);
      else next.add(ref);
      return next;
    });
  };

  const handleAcceptSelected = async () => {
    if (!currentProposal || isReadOnly || accepting) return;

    setAccepting(true);
    setError(null);

    try {
      const payload = {
        base_revision: currentRevision,
        selected_function_refs: Array.from(selectedFunctionRefs),
        selected_task_refs: Array.from(selectedTaskRefs),
      };

      const { data: res } = await apiFetch<PlanAcceptResponseDto>(
        `/events/${event.id}/ai/proposals/${currentProposal.proposal_id}/accept`,
        {
          method: "POST",
          json: payload,
        },
      );

      setAcceptanceSuccess(res);
      setCurrentRevision(res.new_revision);
      setCurrentProposal((prev) => (prev ? { ...prev, status: "accepted" } : null));
    } catch (err) {
      setError(getApiErrorMessage(err, "Failed to accept proposal"));
    } finally {
      setAccepting(false);
    }
  };

  const handleRejectProposal = async () => {
    if (!currentProposal || isReadOnly || rejecting) return;

    setRejecting(true);
    setError(null);

    try {
      await apiFetch<void>(
        `/events/${event.id}/ai/proposals/${currentProposal.proposal_id}/reject`,
        {
          method: "POST",
        },
      );

      setCurrentProposal((prev) => (prev ? { ...prev, status: "rejected" } : null));
    } catch (err) {
      setError(getApiErrorMessage(err, "Failed to reject proposal"));
    } finally {
      setRejecting(false);
    }
  };

  const isStale = currentProposal && currentRevision > currentProposal.base_revision;

  return (
    <div className="grid gap-6 lg:grid-cols-12">
      {/* Sidebar: Conversations History */}
      <div className="space-y-4 lg:col-span-3">
        <div className="flex items-center justify-between">
          <h2 className="flex items-center gap-2 text-sm font-semibold tracking-wide text-muted-foreground uppercase">
            <History className="h-4 w-4" /> Conversations
          </h2>
          {!isReadOnly && (
            <Button
              variant="outline"
              size="sm"
              onClick={handleStartNewConversation}
              className="h-8 gap-1 text-xs"
            >
              <Plus className="h-3.5 w-3.5" /> New
            </Button>
          )}
        </div>

        <div className="space-y-1">
          {conversations.length === 0 ? (
            <p className="rounded-md border border-dashed p-4 text-center text-xs text-muted-foreground">
              No previous conversations. Start planning with PlanAI below!
            </p>
          ) : (
            conversations.map((c) => {
              const active = c.id === activeConversationId;
              return (
                <button
                  type="button"
                  key={c.id}
                  onClick={() => {
                    setActiveConversationId(c.id);
                    setAcceptanceSuccess(null);
                  }}
                  className={`flex w-full items-start gap-2 rounded-lg p-3 text-left transition-colors ${
                    active
                      ? "bg-primary text-primary-foreground font-medium"
                      : "hover:bg-secondary text-foreground border"
                  }`}
                >
                  <MessageSquare className="mt-0.5 h-4 w-4 shrink-0" />
                  <div className="min-w-0 flex-1">
                    <p className="truncate text-sm">{c.title || "Wedding Planning"}</p>
                    <p
                      className={`text-xs ${
                        active ? "text-primary-foreground/80" : "text-muted-foreground"
                      }`}
                    >
                      {new Date(c.updated_at).toLocaleDateString("en-IN", {
                        month: "short",
                        day: "numeric",
                      })}
                    </p>
                  </div>
                </button>
              );
            })
          )}
        </div>
      </div>

      {/* Main Area: Chat & Plan Proposals */}
      <div className="space-y-6 lg:col-span-9">
        {error && (
          <div role="alert" className="flex items-center gap-2 rounded-md border border-destructive/50 bg-destructive/10 p-4 text-sm text-destructive">
            <AlertCircle className="h-4 w-4 shrink-0" />
            <span>{error}</span>
          </div>
        )}

        {acceptanceSuccess && (
          <div role="status" className="flex items-center gap-2 rounded-md border border-emerald-500/50 bg-emerald-500/10 p-4 text-sm text-emerald-800">
            <Check className="h-4 w-4 shrink-0" />
            <span>
              Successfully saved {acceptanceSuccess.accepted_functions_count} ceremonies and{" "}
              {acceptanceSuccess.accepted_tasks_count} starter tasks to your event itinerary!
            </span>
          </div>
        )}

        {/* Existing Messages in Conversation */}
        {loadingConversation ? (
          <div className="flex h-32 items-center justify-center">
            <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
          </div>
        ) : activeConversation?.messages && activeConversation.messages.length > 0 ? (
          <div className="space-y-4">
            {activeConversation.messages.map((m) => {
              if (m.role === "system_metadata") return null;
              const isUser = m.role === "user";
              return (
                <div
                  key={m.id}
                  className={`flex gap-3 ${isUser ? "justify-end" : "justify-start"}`}
                >
                  {!isUser && (
                    <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-primary/10 text-primary">
                      <Sparkles className="h-4 w-4" />
                    </div>
                  )}
                  <div
                    className={`max-w-2xl rounded-lg p-4 text-sm ${
                      isUser
                        ? "bg-primary text-primary-foreground font-medium"
                        : "border bg-card text-foreground"
                    }`}
                  >
                    <p className="whitespace-pre-wrap">{m.content}</p>
                    <span
                      className={`mt-2 block text-right text-[10px] ${
                        isUser ? "text-primary-foreground/75" : "text-muted-foreground"
                      }`}
                    >
                      {new Date(m.created_at).toLocaleTimeString("en-IN", {
                        hour: "2-digit",
                        minute: "2-digit",
                      })}
                    </span>
                  </div>
                </div>
              );
            })}
          </div>
        ) : (
          <Card className="border-dashed bg-gradient-to-br from-primary/5 via-background to-secondary/10 p-8 text-center">
            <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-full bg-primary/10 text-primary">
              <Sparkles className="h-7 w-7" />
            </div>
            <h3 className="mt-4 text-xl font-semibold">PlanAI Wedding Assistant</h3>
            <p className="mx-auto mt-2 max-w-lg text-sm text-muted-foreground">
              Describe your celebration dreams, guest requirements, multi-day ceremonies, or specific traditions.
              PlanAI will generate structured recommendations, venues, and starter tasks tailored to your preferences.
            </p>
          </Card>
        )}

        {/* Proposal Review Card (if available) */}
        {currentProposal && (
          <Card className="border-primary/30 shadow-md">
            <CardHeader className="bg-primary/5 pb-4">
              <div className="flex flex-wrap items-center justify-between gap-2">
                <div className="flex items-center gap-2">
                  <Sparkles className="h-5 w-5 text-primary" />
                  <CardTitle className="text-xl">AI-Generated Plan Proposal</CardTitle>
                </div>
                <div className="flex items-center gap-2">
                  <Badge
                    variant={
                      currentProposal.status === "accepted"
                        ? "success"
                        : currentProposal.status === "rejected"
                        ? "warning"
                        : "outline"
                    }
                  >
                    {currentProposal.status.toUpperCase()}
                  </Badge>
                  {isStale && (
                    <Badge variant="warning" className="flex items-center gap-1">
                      <AlertTriangle className="h-3 w-3" /> Stale Revision
                    </Badge>
                  )}
                </div>
              </div>
              <CardDescription className="mt-2 text-sm font-normal text-foreground">
                {currentProposal.payload.summary}
              </CardDescription>
            </CardHeader>

            <CardContent className="space-y-6 pt-6">
              {/* Assumptions & Warnings */}
              {(currentProposal.payload.assumptions.length > 0 ||
                currentProposal.payload.warnings.length > 0) && (
                <div className="grid gap-4 md:grid-cols-2">
                  {currentProposal.payload.assumptions.length > 0 && (
                    <div className="rounded-lg border bg-secondary/30 p-4">
                      <h4 className="flex items-center gap-2 text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                        <Info className="h-4 w-4 text-primary" /> Planning Assumptions
                      </h4>
                      <ul className="mt-2 list-inside list-disc space-y-1 text-xs text-muted-foreground">
                        {currentProposal.payload.assumptions.map((a, i) => (
                          <li key={i}>{a}</li>
                        ))}
                      </ul>
                    </div>
                  )}

                  {currentProposal.payload.warnings.length > 0 && (
                    <div className="rounded-lg border border-amber-500/30 bg-amber-500/10 p-4 text-amber-900">
                      <h4 className="flex items-center gap-2 text-xs font-semibold uppercase tracking-wider">
                        <AlertTriangle className="h-4 w-4 text-amber-600" /> Important Considerations
                      </h4>
                      <ul className="mt-2 list-inside list-disc space-y-1 text-xs">
                        {currentProposal.payload.warnings.map((w, i) => (
                          <li key={i}>{w}</li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>
              )}

              {/* Proposed Functions Selection */}
              <div>
                <div className="flex items-center justify-between pb-2">
                  <h4 className="flex items-center gap-2 font-semibold">
                    <Calendar className="h-4 w-4 text-primary" /> Proposed Ceremonies & Functions (
                    {selectedFunctionRefs.size}/{currentProposal.payload.proposed_functions.length})
                  </h4>
                  {currentProposal.status === "proposed" && !isReadOnly && (
                    <Button
                      variant="ghost"
                      size="sm"
                      className="text-xs text-primary"
                      onClick={() => {
                        if (
                          selectedFunctionRefs.size ===
                          currentProposal.payload.proposed_functions.length
                        ) {
                          setSelectedFunctionRefs(new Set());
                        } else {
                          setSelectedFunctionRefs(
                            new Set(currentProposal.payload.proposed_functions.map((f) => f.client_ref)),
                          );
                        }
                      }}
                    >
                      {selectedFunctionRefs.size === currentProposal.payload.proposed_functions.length
                        ? "Deselect All"
                        : "Select All"}
                    </Button>
                  )}
                </div>

                <div className="grid gap-3 sm:grid-cols-2">
                  {currentProposal.payload.proposed_functions.map((fn) => {
                    const selected = selectedFunctionRefs.has(fn.client_ref);
                    return (
                      <div
                        key={fn.client_ref}
                        onClick={() => {
                          if (currentProposal.status === "proposed" && !isReadOnly) {
                            toggleFunctionSelection(fn.client_ref);
                          }
                        }}
                        className={`flex items-start gap-3 rounded-lg border p-3 transition-colors ${
                          selected
                            ? "border-primary bg-primary/5"
                            : "border-input bg-card opacity-80"
                        } ${
                          currentProposal.status === "proposed" && !isReadOnly
                            ? "cursor-pointer"
                            : ""
                        }`}
                      >
                        <div className="mt-0.5 text-primary">
                          {selected ? (
                            <CheckSquare className="h-4 w-4" />
                          ) : (
                            <Square className="h-4 w-4 text-muted-foreground" />
                          )}
                        </div>
                        <div className="min-w-0 flex-1">
                          <p className="font-medium text-sm text-foreground">{fn.name}</p>
                          {fn.location_name && (
                            <p className="text-xs text-muted-foreground">{fn.location_name}</p>
                          )}
                          {fn.notes && (
                            <p className="mt-1 text-xs text-muted-foreground/90 italic">
                              {fn.notes}
                            </p>
                          )}
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>

              {/* Proposed Tasks Selection */}
              <div>
                <div className="flex items-center justify-between pb-2">
                  <h4 className="flex items-center gap-2 font-semibold">
                    <ListTodo className="h-4 w-4 text-primary" /> Recommended Starter Tasks (
                    {selectedTaskRefs.size}/{currentProposal.payload.proposed_tasks.length})
                  </h4>
                  {currentProposal.status === "proposed" && !isReadOnly && (
                    <Button
                      variant="ghost"
                      size="sm"
                      className="text-xs text-primary"
                      onClick={() => {
                        if (
                          selectedTaskRefs.size === currentProposal.payload.proposed_tasks.length
                        ) {
                          setSelectedTaskRefs(new Set());
                        } else {
                          setSelectedTaskRefs(
                            new Set(currentProposal.payload.proposed_tasks.map((t) => t.client_ref)),
                          );
                        }
                      }}
                    >
                      {selectedTaskRefs.size === currentProposal.payload.proposed_tasks.length
                        ? "Deselect All"
                        : "Select All"}
                    </Button>
                  )}
                </div>

                <div className="space-y-2">
                  {currentProposal.payload.proposed_tasks.map((task) => {
                    const selected = selectedTaskRefs.has(task.client_ref);
                    return (
                      <div
                        key={task.client_ref}
                        onClick={() => {
                          if (currentProposal.status === "proposed" && !isReadOnly) {
                            toggleTaskSelection(task.client_ref);
                          }
                        }}
                        className={`flex items-start gap-3 rounded-lg border p-3 transition-colors ${
                          selected
                            ? "border-primary bg-primary/5"
                            : "border-input bg-card opacity-80"
                        } ${
                          currentProposal.status === "proposed" && !isReadOnly
                            ? "cursor-pointer"
                            : ""
                        }`}
                      >
                        <div className="mt-0.5 text-primary">
                          {selected ? (
                            <CheckSquare className="h-4 w-4" />
                          ) : (
                            <Square className="h-4 w-4 text-muted-foreground" />
                          )}
                        </div>
                        <div className="min-w-0 flex-1">
                          <div className="flex items-center gap-2">
                            <span className="font-medium text-sm text-foreground">{task.title}</span>
                            <Badge variant="outline" className="text-[10px] uppercase">
                              {task.priority}
                            </Badge>
                          </div>
                          {task.description && (
                            <p className="mt-1 text-xs text-muted-foreground">
                              {task.description}
                            </p>
                          )}
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>

              {/* Theme & Follow-up questions */}
              {currentProposal.payload.follow_up_questions.length > 0 && (
                <div className="rounded-lg border bg-secondary/20 p-4">
                  <h4 className="flex items-center gap-2 text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                    <HelpCircle className="h-4 w-4 text-primary" /> Follow-up Questions for Next Planning Step
                  </h4>
                  <ul className="mt-2 list-inside list-disc space-y-1 text-xs text-muted-foreground">
                    {currentProposal.payload.follow_up_questions.map((q, i) => (
                      <li key={i}>{q}</li>
                    ))}
                  </ul>
                </div>
              )}
            </CardContent>

            {currentProposal.status === "proposed" && !isReadOnly && (
              <CardFooter className="flex flex-wrap items-center justify-between gap-3 border-t bg-secondary/10 p-4">
                <Button
                  variant="outline"
                  onClick={handleRejectProposal}
                  disabled={rejecting || accepting}
                  className="text-destructive hover:bg-destructive/10"
                >
                  {rejecting ? "Rejecting..." : "Decline Proposal"}
                </Button>

                <Button
                  onClick={handleAcceptSelected}
                  disabled={
                    accepting ||
                    rejecting ||
                    (selectedFunctionRefs.size === 0 && selectedTaskRefs.size === 0)
                  }
                  className="gap-2"
                >
                  {accepting ? (
                    <>
                      <Loader2 className="h-4 w-4 animate-spin" /> Saving to Itinerary...
                    </>
                  ) : (
                    <>
                      <Check className="h-4 w-4" /> Accept Selected ({selectedFunctionRefs.size + selectedTaskRefs.size})
                    </>
                  )}
                </Button>
              </CardFooter>
            )}
          </Card>
        )}

        {/* Input prompt bar */}
        {!isReadOnly && (
          <form onSubmit={handleGeneratePlan} className="sticky bottom-4 z-10">
            <div className="flex gap-2 rounded-xl border bg-card/95 p-2 shadow-lg backdrop-blur">
              <Input
                placeholder="Ask PlanAI: e.g. Suggest a 3-day itinerary with Mehendi, Sangeet and Pheras..."
                value={userPrompt}
                onChange={(e) => setUserPrompt(e.target.value)}
                disabled={generating}
                className="border-0 shadow-none focus-visible:ring-0 text-sm"
              />
              <Button type="submit" disabled={!userPrompt.trim() || generating} size="sm">
                {generating ? (
                  <>
                    <Loader2 className="mr-1.5 h-4 w-4 animate-spin" /> Thinking...
                  </>
                ) : (
                  <>
                    <Sparkles className="mr-1.5 h-4 w-4" /> Generate
                  </>
                )}
              </Button>
            </div>
          </form>
        )}
      </div>
    </div>
  );
}
