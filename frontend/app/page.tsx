import type { Metadata } from "next";
import { canonical } from "../lib/seo";
import { Shell } from "../components/Shell";
import { HomeDashboard } from "../components/HomeDashboard";

export const metadata: Metadata = {
  alternates: { canonical: canonical("/") },
};

export default function Home() {
  return (
    <Shell>
      <HomeDashboard />
    </Shell>
  );
}
