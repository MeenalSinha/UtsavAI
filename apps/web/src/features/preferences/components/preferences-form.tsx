"use client";

import { Check, Loader2, Plus, Sparkles, X } from "lucide-react";
import * as React from "react";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { apiFetch } from "@/lib/api/client";
import { getApiErrorMessage } from "@/lib/api/errors";
import type { EventDto, EventPreferencesDto } from "@/types/api";

const PRESET_STYLES = [
  "Traditional",
  "Modern",
  "Minimalist",
  "Royal & Grand",
  "Contemporary",
  "Rustic",
  "Eco-Friendly",
  "Intimate & Cozy",
  "Bollywood Glam",
  "Fusion",
];

const PRESET_PRIORITIES = [
  "Guest Experience & Hospitality",
  "Budget Optimization",
  "Traditional Authenticity",
  "Catering & Culinary Variety",
  "Photography & Memories",
  "Music & Entertainment",
  "Sustainability & Zero Waste",
  "Accessibility & Elder Comfort",
];

const PRESET_ACCESSIBILITY = [
  "Wheelchair accessible venues",
  "Dedicated seating for elderly",
  "Strict Vegetarian / Jain food options",
  "Halal food options",
  "Nut / Allergy-safe catering",
  "Quiet lounge for elders / kids",
  "Golf cart / Buggy transport on-site",
];

interface PreferencesFormProps {
  event: EventDto;
  initialPreferences: EventPreferencesDto | null;
}

export function PreferencesForm({ event, initialPreferences }: PreferencesFormProps) {
  const isReadOnly = event.status === "archived" || event.my_role === "viewer";

  const [styleTags, setStyleTags] = React.useState<string[]>(
    initialPreferences?.style_tags || ["Traditional"],
  );
  const [customTagInput, setCustomTagInput] = React.useState("");

  const [culturalTradition, setCulturalTradition] = React.useState<string>(
    (initialPreferences?.cultural_context?.tradition as string) || "Hindu / Vedic",
  );
  const [regionalCustoms, setRegionalCustoms] = React.useState<string>(
    (initialPreferences?.cultural_context?.regional_customs as string) || "",
  );
  const [specialCeremonies, setSpecialCeremonies] = React.useState<string>(
    (initialPreferences?.cultural_context?.special_ceremonies as string) || "",
  );

  const [selectedPriorities, setSelectedPriorities] = React.useState<string[]>(
    (initialPreferences?.priorities?.key_priorities as string[]) || ["Guest Experience & Hospitality", "Traditional Authenticity"],
  );
  const [priorityNotes, setPriorityNotes] = React.useState<string>(
    (initialPreferences?.priorities?.notes as string) || "",
  );

  const [selectedAccessibility, setSelectedAccessibility] = React.useState<string[]>(
    (initialPreferences?.accessibility_notes?.accommodations as string[]) || ["Dedicated seating for elderly"],
  );
  const [accessibilityNotes, setAccessibilityNotes] = React.useState<string>(
    (initialPreferences?.accessibility_notes?.additional_notes as string) || "",
  );

  const [saving, setSaving] = React.useState(false);
  const [savedSuccess, setSavedSuccess] = React.useState(false);
  const [error, setError] = React.useState<string | null>(null);

  const toggleStyleTag = (tag: string) => {
    if (isReadOnly) return;
    setStyleTags((prev) =>
      prev.includes(tag) ? prev.filter((t) => t !== tag) : [...prev, tag],
    );
  };

  const addCustomTag = () => {
    const trimmed = customTagInput.trim();
    if (trimmed && !styleTags.includes(trimmed)) {
      setStyleTags((prev) => [...prev, trimmed]);
      setCustomTagInput("");
    }
  };

  const togglePriority = (priority: string) => {
    if (isReadOnly) return;
    setSelectedPriorities((prev) =>
      prev.includes(priority) ? prev.filter((p) => p !== priority) : [...prev, priority],
    );
  };

  const toggleAccessibility = (item: string) => {
    if (isReadOnly) return;
    setSelectedAccessibility((prev) =>
      prev.includes(item) ? prev.filter((i) => i !== item) : [...prev, item],
    );
  };

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault();
    if (isReadOnly) return;

    setSaving(true);
    setError(null);
    setSavedSuccess(false);

    try {
      const payload = {
        style_tags: styleTags,
        cultural_context: {
          tradition: culturalTradition,
          regional_customs: regionalCustoms,
          special_ceremonies: specialCeremonies,
        },
        priorities: {
          key_priorities: selectedPriorities,
          notes: priorityNotes,
        },
        accessibility_notes: {
          accommodations: selectedAccessibility,
          additional_notes: accessibilityNotes,
        },
        schema_version: 1,
      };

      await apiFetch<EventPreferencesDto>(`/events/${event.id}/preferences`, {
        method: "PUT",
        json: payload,
      });

      setSavedSuccess(true);
      setTimeout(() => setSavedSuccess(false), 3000);
    } catch (err) {
      setError(getApiErrorMessage(err, "Failed to save event preferences"));
    } finally {
      setSaving(false);
    }
  };

  return (
    <form onSubmit={handleSave} className="space-y-6">
      {error && (
        <div role="alert" className="rounded-md border border-destructive/50 bg-destructive/10 p-4 text-sm text-destructive">
          {error}
        </div>
      )}

      {savedSuccess && (
        <div role="status" className="flex items-center gap-2 rounded-md border border-emerald-500/50 bg-emerald-500/10 p-4 text-sm text-emerald-800">
          <Check className="h-4 w-4" /> Preferences saved successfully. PlanAI will use these in upcoming plan proposals.
        </div>
      )}

      {/* Style Preferences */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-xl">
            <Sparkles className="h-5 w-5 text-primary" /> Aesthetic & Style Theme
          </CardTitle>
          <CardDescription>
            Select aesthetic styles that best match your celebration vision.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex flex-wrap gap-2">
            {PRESET_STYLES.map((style) => {
              const selected = styleTags.includes(style);
              return (
                <button
                  type="button"
                  key={style}
                  onClick={() => toggleStyleTag(style)}
                  disabled={isReadOnly}
                  className={`inline-flex items-center rounded-full border px-3 py-1.5 text-sm font-medium transition-colors ${
                    selected
                      ? "border-primary bg-primary text-primary-foreground"
                      : "border-input bg-background hover:bg-secondary text-foreground"
                  } ${isReadOnly ? "cursor-not-allowed opacity-70" : "cursor-pointer"}`}
                >
                  {selected && <Check className="mr-1.5 h-3.5 w-3.5" />}
                  {style}
                </button>
              );
            })}
          </div>

          {!isReadOnly && (
            <div className="flex max-w-sm items-center gap-2 pt-2">
              <Input
                placeholder="Add custom style tag..."
                value={customTagInput}
                onChange={(e) => setCustomTagInput(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === "Enter") {
                    e.preventDefault();
                    addCustomTag();
                  }
                }}
              />
              <Button type="button" variant="outline" size="sm" onClick={addCustomTag}>
                <Plus className="h-4 w-4" /> Add
              </Button>
            </div>
          )}

          {styleTags.filter((t) => !PRESET_STYLES.includes(t)).length > 0 && (
            <div className="flex flex-wrap gap-2 pt-2">
              <span className="text-xs text-muted-foreground self-center">Custom tags:</span>
              {styleTags
                .filter((t) => !PRESET_STYLES.includes(t))
                .map((tag) => (
                  <span
                    key={tag}
                    className="inline-flex items-center gap-1 rounded-full bg-secondary px-3 py-1 text-xs font-medium text-secondary-foreground"
                  >
                    {tag}
                    {!isReadOnly && (
                      <button
                        type="button"
                        onClick={() => toggleStyleTag(tag)}
                        className="hover:text-destructive"
                      >
                        <X className="h-3 w-3" />
                      </button>
                    )}
                  </span>
                ))}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Cultural & Regional Context */}
      <Card>
        <CardHeader>
          <CardTitle className="text-xl">Cultural & Regional Heritage</CardTitle>
          <CardDescription>
            Specify your ceremonies, traditions, and customs so AI proposals respect your family traditions.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="tradition">Primary Tradition or Faith Heritage</Label>
            <Input
              id="tradition"
              disabled={isReadOnly}
              value={culturalTradition}
              onChange={(e) => setCulturalTradition(e.target.value)}
              placeholder="e.g. Hindu (North Indian), Punjabi Sikh, South Indian (Tamil Iyer), Interfaith..."
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="regionalCustoms">Regional Customs & Community Background</Label>
            <Input
              id="regionalCustoms"
              disabled={isReadOnly}
              value={regionalCustoms}
              onChange={(e) => setRegionalCustoms(e.target.value)}
              placeholder="e.g. Marwari customs, Baaraat with Dhol, Sindhi Saanth, Bengali Shubho Drishti..."
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="specialCeremonies">Must-have Rituals & Ceremonies</Label>
            <Input
              id="specialCeremonies"
              disabled={isReadOnly}
              value={specialCeremonies}
              onChange={(e) => setSpecialCeremonies(e.target.value)}
              placeholder="e.g. Ganesh Pujan, Mehendi, Sangeet Night, Haldi, Varmala, Saat Phere, Reception..."
            />
          </div>
        </CardContent>
      </Card>

      {/* Priorities */}
      <Card>
        <CardHeader>
          <CardTitle className="text-xl">Planning Priorities</CardTitle>
          <CardDescription>
            What matters most to you during this celebration?
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid gap-2 sm:grid-cols-2">
            {PRESET_PRIORITIES.map((priority) => {
              const selected = selectedPriorities.includes(priority);
              return (
                <button
                  type="button"
                  key={priority}
                  onClick={() => togglePriority(priority)}
                  disabled={isReadOnly}
                  className={`flex items-center gap-2 rounded-lg border p-3 text-left text-sm transition-colors ${
                    selected
                      ? "border-primary bg-primary/5 font-medium text-primary"
                      : "border-input hover:bg-secondary text-foreground"
                  } ${isReadOnly ? "cursor-not-allowed opacity-70" : "cursor-pointer"}`}
                >
                  <div
                    className={`flex h-4 w-4 shrink-0 items-center justify-center rounded border ${
                      selected ? "border-primary bg-primary text-primary-foreground" : "border-muted-foreground"
                    }`}
                  >
                    {selected && <Check className="h-3 w-3" />}
                  </div>
                  <span>{priority}</span>
                </button>
              );
            })}
          </div>

          <div className="space-y-2 pt-2">
            <Label htmlFor="priorityNotes">Additional Priority Notes</Label>
            <Input
              id="priorityNotes"
              disabled={isReadOnly}
              value={priorityNotes}
              onChange={(e) => setPriorityNotes(e.target.value)}
              placeholder="e.g. We want high emphasis on live musical performances and intimate family moments."
            />
          </div>
        </CardContent>
      </Card>

      {/* Accessibility & Comfort */}
      <Card>
        <CardHeader>
          <CardTitle className="text-xl">Accessibility & Guest Comfort</CardTitle>
          <CardDescription>
            Ensure all family members, elders, and guests are comfortably accommodated.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid gap-2 sm:grid-cols-2">
            {PRESET_ACCESSIBILITY.map((item) => {
              const selected = selectedAccessibility.includes(item);
              return (
                <button
                  type="button"
                  key={item}
                  onClick={() => toggleAccessibility(item)}
                  disabled={isReadOnly}
                  className={`flex items-center gap-2 rounded-lg border p-3 text-left text-sm transition-colors ${
                    selected
                      ? "border-primary bg-primary/5 font-medium text-primary"
                      : "border-input hover:bg-secondary text-foreground"
                  } ${isReadOnly ? "cursor-not-allowed opacity-70" : "cursor-pointer"}`}
                >
                  <div
                    className={`flex h-4 w-4 shrink-0 items-center justify-center rounded border ${
                      selected ? "border-primary bg-primary text-primary-foreground" : "border-muted-foreground"
                    }`}
                  >
                    {selected && <Check className="h-3 w-3" />}
                  </div>
                  <span>{item}</span>
                </button>
              );
            })}
          </div>

          <div className="space-y-2 pt-2">
            <Label htmlFor="accessibilityNotes">Additional Accessibility Notes</Label>
            <Input
              id="accessibilityNotes"
              disabled={isReadOnly}
              value={accessibilityNotes}
              onChange={(e) => setAccessibilityNotes(e.target.value)}
              placeholder="e.g. Grandparents require ground-floor accommodation and step-free access to mandap."
            />
          </div>
        </CardContent>
        {!isReadOnly && (
          <CardFooter className="flex justify-end border-t p-4">
            <Button type="submit" disabled={saving}>
              {saving ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" /> Saving...
                </>
              ) : (
                "Save Preferences"
              )}
            </Button>
          </CardFooter>
        )}
      </Card>
    </form>
  );
}

