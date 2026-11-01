"use client";

export default function GlobalError({ reset }: { error: Error & { digest?: string }; reset: () => void }) {
  return (
    <html lang="en">
      <body style={{ fontFamily: "system-ui, sans-serif", padding: "4rem 1rem", textAlign: "center" }}>
        <h1>UtsavAI is unavailable right now</h1>
        <p>Please try again in a moment.</p>
        <button type="button" onClick={reset} style={{ padding: "0.6rem 1.2rem", marginTop: "1rem" }}>
          Try again
        </button>
      </body>
    </html>
  );
}
