import type { MetadataRoute } from "next";
import { canonical } from "../lib/seo";
export default function robots(): MetadataRoute.Robots {
  return {
    rules: [{userAgent:"*",allow:["/","/about","/our-mission","/data-sources","/disclaimer"],disallow:["/company/","/search","/account/","/portfolio/","/watchlist/","/api/","/_next/"]}],
    sitemap: canonical("/sitemap.xml"),
    host: canonical("/"),
  };
}
