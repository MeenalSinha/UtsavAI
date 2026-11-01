import type { Metadata } from "next";
import Link from "next/link";

import { routes, safeNextPath } from "@/config/routes";
import { AuthCard } from "@/features/auth/components/auth-card";
import { SignInForm } from "@/features/auth/components/forms";

export const metadata: Metadata = { title: "Sign in" };

const NOTICES: Record<string, string> = {
  expired: "Your session has ended. Please sign in again.",
  verified: "Your email is verified. Sign in to continue.",
  callback_error: "That link is invalid or has expired. Please try again.",
};

export default async function SignInPage({ searchParams }: { searchParams: Promise<Record<string, string | undefined>> }) {
  const sp = await searchParams;
  const next = sp.next ? safeNextPath(sp.next) : undefined;
  return (
    <AuthCard
      title="Welcome back"
      description="Sign in to your UtsavAI workspace."
      footer={
        <>
          New to UtsavAI?{" "}
          <Link href={routes.signUp} className="font-medium text-primary hover:underline">
            Create an account
          </Link>
        </>
      }
    >
      <SignInForm next={next} notice={sp.reason ? NOTICES[sp.reason] : undefined} />
    </AuthCard>
  );
}
