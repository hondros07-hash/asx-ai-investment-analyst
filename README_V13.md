# V13 — Investor Documents / PDF-first

User-facing behavior:
- No XML/XBRL files are offered for download.
- US defaults to investor-relevant forms: 10-K, 10-Q, 8-K, 20-F, 40-F, 6-K, ARS, DEF 14A.
- Insider Forms 3/4/5 are hidden from the normal reports view.
- SEC filing indexes are inspected for an actual company-filed `.pdf`.
- If a company-filed PDF exists: View PDF, Summarise, Download company PDF.
- If the SEC filing is official HTML and no PDF was supplied: Summarise the official filing, but do not pretend it is a PDF.
- ASX documents remain PDF-first. Complete/reliable ASX history still requires a ComNews-capable provider.

This deliberately separates regulator technical formats from the investor-facing UI.
