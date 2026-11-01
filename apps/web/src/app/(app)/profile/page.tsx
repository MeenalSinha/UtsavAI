import type { Metadata } from "next";

import { PageHeader } from "@/components/shared/page-header";
import { Card, CardContent } from "@/components/ui/card";
import { routes } from "@/config/routes";
import { ProfileForm } from "@/features/profile/components/profile-form";
import { loadOrNavigate } from "@/lib/api/load";
import { fetchMeta, serverGet } from "@/lib/api/server";
import type { MetaDto, ProfileDto } from "@/types/api";

export const metadata: Metadata = { title: "Profile" };

export default async function ProfilePage() {
  const [profile, meta] = await Promise.all([
    loadOrNavigate(serverGet<ProfileDto>("/me"), routes.profile),
    fetchMeta<MetaDto>(),
  ]);
  return (
    <div className="mx-auto max-w-xl space-y-6">
      <PageHeader title="Your profile" description="How you appear in UtsavAI." />
      <Card>
        <CardContent className="p-6 sm:p-8">
          <ProfileForm profile={profile} meta={meta} />
        </CardContent>
      </Card>
    </div>
  );
}
