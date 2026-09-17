# V19.3 - Phase 4: Report Intelligence

Phase 4 connects the research terminal to company-report evidence.

Features:
- dedicated Report Intelligence workspace
- upload company PDF reports
- fetch a selected latest announcement/report when the source exposes a document URL
- page-by-page PDF text extraction using pypdf
- deterministic evidence summary
- company/sector-specific KPI candidate extraction
- page number + evidence snippet retained with each candidate
- extracted values are NOT automatically treated as facts
- user confirmation required before a KPI enters the evidence ledger
- persistent report metadata and SHA-256 document identity
- duplicate report protection
- confirmed KPI comparison across reporting periods
- integration with Monitor My Thesis
- all Phase 1/2/3 features retained

Limitations:
- image-only/scanned PDFs require OCR and are reported as unsupported in this Streamlit build
- deterministic extraction is intentionally conservative and can miss KPIs
- report comparisons only use user-confirmed KPI observations
- automatic background report ingestion remains a later production feature

Deployment diagnostic:
V19.3 • Market Investment Analyst • Report Intelligence
