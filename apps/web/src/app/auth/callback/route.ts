import type { EmailOtpType } from "@supabase/supabase-js";
import { NextResponse, type NextRequest } from "next/server";

import { routes, safeNextPath } from "@/config/routes";
import { createClient } from "@/lib/supabase/server";

export const dynamic = "force-dynamic";

const OTP_TYPES = new Set<EmailOtpType>(["signup", "recovery", "email", "invite", "magiclink", "email_change"]);

/**
 * Handles both Supabase email flows:
 *  - PKCE: ?code=...             -> exchangeCodeForSession
 *  - token hash: ?token_hash=&type= -> verifyOtp
 * `next` is validated to a same-site relative path (no open redirect).
 */
export async function GET(request: NextRequest) {
  const { searchParams, origin } = request.nextUrl;
  const next = safeNextPath(searchParams.get("next"));
  const fail = () => NextResponse.redirect(`${origin}${routes.signIn}?reason=callback_error`);

  const supabase = await createClient();
  const code = searchParams.get("code");
  const tokenHash = searchParams.get("token_hash");
  const type = searchParams.get("type") as EmailOtpType | null;

  if (code) {
    const { error } = await supabase.auth.exchangeCodeForSession(code);
    return error ? fail() : NextResponse.redirect(`${origin}${next}`);
  }
  if (tokenHash && type && OTP_TYPES.has(type)) {
    const { error } = await supabase.auth.verifyOtp({ type, token_hash: tokenHash });
    if (error) return fail();
    return NextResponse.redirect(`${origin}${type === "recovery" ? routes.resetPassword : next}`);
  }
  return fail();
}
