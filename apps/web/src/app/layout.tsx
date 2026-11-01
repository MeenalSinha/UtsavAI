import type { Metadata, Viewport } from "next";
import * as React from "react";

import { Toaster } from "@/components/ui/sonner";

import "./globals.css";

export const metadata: Metadata = {
  title: { default: "UtsavAI - Plan every celebration", template: "%s | UtsavAI" },
  description: "UtsavAI helps you plan, budget and coordinate weddings and celebrations in one private workspace.",
};

export const viewport: Viewport = { themeColor: "#7a1f3d", width: "device-width", initialScale: 1 };

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en-IN">
      <body>
        {children}
        <Toaster />
      </body>
    </html>
  );
}
