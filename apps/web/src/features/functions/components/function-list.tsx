"use client";

import { Calendar, Clock, MapPin, Pencil, Plus, Trash2 } from "lucide-react";
import * as React from "react";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { FunctionDeleteDialog } from "@/features/functions/components/function-delete-dialog";
import { FunctionDialog } from "@/features/functions/components/function-dialog";
import type { EventDto, EventFunctionDto } from "@/types/api";

interface FunctionListProps {
  event: EventDto;
  initialFunctions: EventFunctionDto[];
}

function formatFnTime(isoStr: string | null): string {
  if (!isoStr) return "TBD";
  try {
    const d = new Date(isoStr);
    return d.toLocaleString("en-IN", {
      month: "short",
      day: "numeric",
      hour: "numeric",
      minute: "2-digit",
      hour12: true,
    });
  } catch {
    return isoStr;
  }
}

export function FunctionList({ event, initialFunctions }: FunctionListProps) {
  const [functions, setFunctions] = React.useState<EventFunctionDto[]>(
    [...initialFunctions].sort((a, b) => a.sort_order - b.sort_order),
  );

  const [dialogOpen, setDialogOpen] = React.useState(false);
  const [selectedFn, setSelectedFn] = React.useState<EventFunctionDto | null>(null);

  const [deleteDialogOpen, setDeleteDialogOpen] = React.useState(false);
  const [deletingFn, setDeletingFn] = React.useState<EventFunctionDto | null>(null);

  const isReadOnly = event.status === "archived" || event.my_role === "viewer";

  const handleOpenAdd = () => {
    setSelectedFn(null);
    setDialogOpen(true);
  };

  const handleOpenEdit = (fn: EventFunctionDto) => {
    setSelectedFn(fn);
    setDialogOpen(true);
  };

  const handleOpenDelete = (fn: EventFunctionDto) => {
    setDeletingFn(fn);
    setDeleteDialogOpen(true);
  };

  const handleSaved = (saved: EventFunctionDto) => {
    setFunctions((prev) => {
      const idx = prev.findIndex((f) => f.id === saved.id);
      let updated: EventFunctionDto[];
      if (idx >= 0) {
        updated = [...prev];
        updated[idx] = saved;
      } else {
        updated = [...prev, saved];
      }
      return updated.sort((a, b) => a.sort_order - b.sort_order);
    });
  };

  const handleDeleted = (deletedId: string) => {
    setFunctions((prev) => prev.filter((f) => f.id !== deletedId));
  };

  const nextSortOrder = functions.length > 0 ? Math.max(...functions.map((f) => f.sort_order)) + 1 : 0;

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-xl font-semibold">Wedding Ceremonies & Functions</h2>
          <p className="text-sm text-muted-foreground">
            {functions.length} {functions.length === 1 ? "function" : "functions"} planned for this celebration.
          </p>
        </div>
        {!isReadOnly && (
          <Button onClick={handleOpenAdd} size="sm">
            <Plus className="mr-1.5 h-4 w-4" /> Add Function
          </Button>
        )}
      </div>

      {functions.length === 0 ? (
        <Card className="border-dashed p-10 text-center">
          <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-full bg-primary/10 text-primary">
            <Calendar className="h-6 w-6" />
          </div>
          <h3 className="mt-4 text-lg font-medium">No functions added yet</h3>
          <p className="mt-1 text-sm text-muted-foreground">
            Get started by adding ceremonies manually, or use PlanAI to recommend a structured itinerary.
          </p>
          {!isReadOnly && (
            <div className="mt-6 flex justify-center gap-3">
              <Button onClick={handleOpenAdd}>
                <Plus className="mr-1.5 h-4 w-4" /> Add First Function
              </Button>
            </div>
          )}
        </Card>
      ) : (
        <div className="grid gap-4 md:grid-cols-2">
          {functions.map((fn, idx) => (
            <Card key={fn.id} className="relative transition-shadow hover:shadow-sm">
              <CardHeader className="pb-3">
                <div className="flex items-start justify-between">
                  <div>
                    <span className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                      Sequence #{idx + 1}
                    </span>
                    <CardTitle className="text-lg font-semibold">{fn.name}</CardTitle>
                  </div>
                  {!isReadOnly && (
                    <div className="flex items-center gap-1">
                      <Button
                        variant="ghost"
                        size="icon"
                        className="h-8 w-8 text-muted-foreground hover:text-foreground"
                        onClick={() => handleOpenEdit(fn)}
                      >
                        <Pencil className="h-4 w-4" />
                        <span className="sr-only">Edit {fn.name}</span>
                      </Button>
                      <Button
                        variant="ghost"
                        size="icon"
                        className="h-8 w-8 text-muted-foreground hover:text-destructive"
                        onClick={() => handleOpenDelete(fn)}
                      >
                        <Trash2 className="h-4 w-4" />
                        <span className="sr-only">Delete {fn.name}</span>
                      </Button>
                    </div>
                  )}
                </div>
              </CardHeader>
              <CardContent className="space-y-2 text-sm">
                <div className="flex items-center gap-2 text-muted-foreground">
                  <Clock className="h-4 w-4 shrink-0 text-primary" />
                  <span>
                    {formatFnTime(fn.starts_at)} {fn.ends_at ? `– ${formatFnTime(fn.ends_at)}` : ""}
                  </span>
                </div>

                {fn.location_name && (
                  <div className="flex items-center gap-2 text-muted-foreground">
                    <MapPin className="h-4 w-4 shrink-0 text-primary" />
                    <span>{fn.location_name}</span>
                  </div>
                )}

                {fn.notes && (
                  <p className="mt-2 rounded-md bg-secondary/50 p-2 text-xs text-secondary-foreground">
                    {fn.notes}
                  </p>
                )}
              </CardContent>
            </Card>
          ))}
        </div>
      )}

      <FunctionDialog
        eventId={event.id}
        fn={selectedFn}
        open={dialogOpen}
        onOpenChange={setDialogOpen}
        onSuccess={handleSaved}
        nextSortOrder={nextSortOrder}
      />

      <FunctionDeleteDialog
        eventId={event.id}
        fn={deletingFn}
        open={deleteDialogOpen}
        onOpenChange={setDeleteDialogOpen}
        onSuccess={handleDeleted}
      />
    </div>
  );
}
