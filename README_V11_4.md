# V11.4 — Reports & Filings Library

Adds a Reports & Filings workspace for the selected company.

- ASX listings: attempts official ASX announcement/report retrieval.
- US listings: uses official SEC EDGAR submissions and filing documents.
- Historical report table with date, filing/report type, title and source.
- Text filtering.
- Click/select a report and load an extractive summary grounded in the document text.
- Download the original retrieved report from inside the application.
- The summariser is deliberately extractive in this build; it does not invent unavailable figures.

Note: ASX endpoint availability and document URL formats can change. Production should add a maintained/licensed ASX announcements adapter and persistent document cache.
