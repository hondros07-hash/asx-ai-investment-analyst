# V12.1 — Announcement Source Reliability Fix

Fixes:
1. SEC EDGAR requests no longer advertise gzip without decoding it.
2. Search terms such as `annual report` map to SEC 10-K/20-F/40-F and `quarterly report` maps to 10-Q.
3. ASX fallback no longer uses the invalid year-query logic from V12.
4. ASX parser recognizes `displayAnnouncement.do` document links.
5. Empty states now distinguish an unavailable ASX website fallback from a genuine provider-backed feed.

Important: complete CommSec-style ASX announcement history still requires an authorised ComNews-capable source. The public ASX website fallback is best-effort only.
