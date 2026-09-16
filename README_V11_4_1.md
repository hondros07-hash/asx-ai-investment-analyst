# V11.4.1 — ASX Reports Hotfix

The V11.4 ASX adapter incorrectly assumed a JSON company-announcements endpoint. V11.4.1 switches ASX retrieval to the official historical-announcements search used by ASX itself, queries calendar years individually, parses official announcement rows and preserves direct ASX PDF URLs for summaries/downloads.

US SEC EDGAR behaviour is unchanged.

Known limitation: historical ASX ticker/code changes may require searching the legacy code as well. A future security-master layer should automate code-history mapping.
