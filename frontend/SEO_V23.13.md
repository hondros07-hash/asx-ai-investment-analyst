# AXÍA V23.13 — SEO foundation

## Scope
Next.js public pages are server-rendered and carry unique titles, descriptions and canonical URLs. The homepage, About, Our Mission, Data Sources and Disclaimer are the only sitemap entries. Search and company research routes carry noindex metadata. No ticker pages are submitted to the sitemap until verified issuer identity, substantive server-rendered content and unique canonical routes are ready.

## Deployment and verification
1. Merge and deploy the Next.js frontend first. The current Streamlit host does not automatically serve Next.js metadata routes. Do not point the production domain at this incomplete frontend solely for SEO.
2. Set `AXIA_SITE_URL` to the verified production origin (default https://axiaindex.com). Use a separate staging origin and block staging indexing at the host.
3. Run `npm install && npm run lint && npm run build` in frontend.
4. Fetch `/robots.txt` and `/sitemap.xml` on the actual deployed domain; confirm they serve HTTP 200 with the intended content and canonical host.
5. Inspect rendered HTML for each public page's title, description, canonical and JSON-LD; verify noindex on /search and /company/ZIP.AX/overview.
6. Set up Google Search Console for the verified domain, submit the sitemap and inspect index coverage. Sitemap submission is not an indexing guarantee.
7. Confirm public content, links, mobile usability and Core Web Vitals before domain cutover.

## Caveats
robots.txt is crawler guidance, not access control. Sensitive account and portfolio routes require server-side authentication. Public informational copy is an initial foundation, not a complete migration of the existing Streamlit legal pages. Verify wording with the current legal content before production. Do not generate fictional review ratings, investment recommendations, company profiles or dynamic sitemaps from unverified tickers.
