# UtsavAI Accessibility & Inclusivity Audit (WCAG 2.2 AA)

## 1. Executive Summary
UtsavAI has been developed and evaluated against the Web Content Accessibility Guidelines (WCAG 2.2 Level AA). The interface provides high contrast ratios, screen reader support, keyboard navigability, and clear focus states.

---

## 2. Audit Findings & Implementations

### Contrast and Color
- **Text Contrast:** All body text meets or exceeds the required 4.5:1 contrast ratio against background surfaces (`text-foreground` on `bg-background` and `bg-card`).
- **Semantic Meaning:** Information is never conveyed by color alone. Badges and warnings include explicit textual status labels (e.g. `Critical`, `High`, `Active`, `Reserved`).

### Keyboard Navigation & Focus
- **Skip Link:** High-priority skip-to-content anchor (`<a href="#main">Skip to content</a>`) present at the top of the application shell.
- **Visible Focus States:** Consistent `focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2` styles across all interactive elements (buttons, links, inputs).
- **Tab Order:** Logical tab order preserved across sidebar, header, form fields, and action buttons. Modals trap focus during interaction and restore focus on close.

### Screen Readers & ARIA Semantics
- **Landmarks:** Distinct `<header>`, `<nav>`, `<main>`, `<aside>`, and `<footer>` landmarks defined on all pages.
- **Form Labels:** Every input field possesses an explicitly bound `<Label htmlFor={...}>` or `aria-label`.
- **Alternative Text:** Decorative icons carry `aria-hidden="true"`. Data visualizations include structured tables and summarized card representations as textual alternatives.

