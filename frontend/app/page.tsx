import type { Metadata } from "next";
import { canonical } from "../lib/seo";
import { HomeReferenceShell } from "../components/HomeReferenceShell";
import { HomeDashboardReference } from "../components/HomeDashboardReference";

export const metadata: Metadata = {
  alternates: { canonical: canonical("/") },
};

export default function Home() {
  return (
    <HomeReferenceShell>
      <HomeDashboardReference />
    </HomeReferenceShell>
  );
}
