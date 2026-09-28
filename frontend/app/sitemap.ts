import type { MetadataRoute } from "next";
import { canonical, publicRoutes } from "../lib/seo";
export default function sitemap(): MetadataRoute.Sitemap {
  return publicRoutes.map(path => ({
    url: canonical(path),
    changeFrequency: path === "/" ? "weekly" : "monthly",
    priority: path === "/" ? 1 : 0.5,
  }));
}
