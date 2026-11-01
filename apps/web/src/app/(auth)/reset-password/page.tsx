import type { Metadata } from "next";
import { redirect } from "next/navigation";

import { routes } from "@/config/routes";
import { AuthCard } from "@/features/auth/components/auth-card";
import { ResetPasswordForm } from "@/features/auth/components/forms";
import { getCurrentUser } from "@/lib/supabase/server";

export const metadata: Metadata = { title: "Choose a new password" };
export const dynamic = "force-dynamic";

export default async function ResetPasswordPage() {
  // Reached only through the emailed recovery link, which establishes a session at /auth/callback.
  const user = await getCurrentUser();
  if (!user) redirect(`${routes.forgotPassword}`);
  return (
    <AuthCard title="Choose a new password" description="Pick something strong that you have not used elsewhere.">
      <ResetPasswordForm />
    </AuthCard>
  );
}
