/** Public canonical origin. Set AXIA_SITE_URL to the verified production origin. */
export const siteUrl = new URL(process.env.AXIA_SITE_URL || "https://axiaindex.com");
export const siteName = "AXÍA";
export const publicRoutes = ["/", "/about", "/our-mission", "/data-sources", "/disclaimer"] as const;
export function canonical(path: string) {
  return new URL(path, siteUrl).toString();
}
