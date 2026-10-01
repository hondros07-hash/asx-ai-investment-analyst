import Link from "next/link";

type Filing = {
  form?: string;
  report_type?: string;
  filing_date?: string;
  description?: string;
  official_document_url?: string;
  document_url?: string;
};

type CoreReports = {
  annual?: Filing[];
  quarterly?: Filing[];
  current?: Filing[];
  foreign?: Filing[];
};

type ReportData = {
  ticker?: string;
  issuer?: string;
  status?: string;
  source?: string;
  checked_at?: string;
  issuer_verified?: boolean;
  filing_count?: number;
  decision_report_count?: number;
  analysis_status?: string;
  message?: string;
  core_reports?: CoreReports;
};

const safeUrl = (value?: string) =>
  typeof value === "string" &&
  /^https:\/\/(www\.)?sec\.gov\//i.test(value)
    ? value
    : null;

function ReportGroup({
  title,
  description,
  reports,
}: {
  title: string;
  description: string;
  reports: Filing[];
}) {
  return (
    <section className="panel">
      <div className="report-section-heading">
        <div>
          <h3>{title}</h3>
          <p className="muted">{description}</p>
        </div>
        <span className="report-count">{reports.length}</span>
      </div>

      {reports.length === 0 ? (
        <p>No verified reports are available in this category.</p>
      ) : (
        <div className="report-list">
          {reports.map((report, index) => {
            const href = safeUrl(
              report.official_document_url || report.document_url
            );

            return (
              <article
                className="research-entry"
                key={`${report.form || "filing"}-${report.filing_date || index}-${index}`}
              >
                <div>
                  <strong>{report.form || "Official filing"}</strong>
                  <span>
                    {report.filing_date || "Date unavailable"}
                    {report.report_type
                      ? ` · ${report.report_type.replaceAll("_", " ")}`
                      : ""}
                  </span>

                  {report.description && (
                    <small>{report.description}</small>
                  )}
                </div>

                {href ? (
                  <a
                    href={href}
                    target="_blank"
                    rel="noopener noreferrer"
                  >
                    View official filing ↗
                  </a>
                ) : (
                  <small>Official document link unavailable</small>
                )}
              </article>
            );
          })}
        </div>
      )}
    </section>
  );
}

export function ReportIntelligence({
  data,
}: {
  data: Record<string, unknown>;
}) {
  const report = data as ReportData;
  const core = report.core_reports || {};

  const annual = Array.isArray(core.annual) ? core.annual : [];
  const quarterly = Array.isArray(core.quarterly) ? core.quarterly : [];
  const current = Array.isArray(core.current) ? core.current : [];
  const foreign = Array.isArray(core.foreign) ? core.foreign : [];

  const verified = report.issuer_verified === true;

  return (
    <div className="report-intelligence">
      <section className="panel">
        <div className="report-intelligence-header">
          <div>
            <div className="eyebrow">
              OFFICIAL FILING INTELLIGENCE
            </div>

            <h3>
              {report.issuer || report.ticker || "Company reports"}
            </h3>

            <p>
              AXÍA identifies decision-useful company filings from
              verified official regulatory sources.
            </p>
          </div>

          <div
            className={
              verified
                ? "verification verified"
                : "verification"
            }
          >
            {verified ? "✓ Issuer verified" : "Issuer not verified"}
          </div>
        </div>

        <div className="research-context">
          <span>
            Source: {report.source || "Unavailable"}
          </span>

          <span>
            Filings indexed:{" "}
            {typeof report.filing_count === "number"
              ? report.filing_count
              : "Unavailable"}
          </span>

          <span>
            Analysis:{" "}
            {report.analysis_status || "Not connected"}
          </span>
        </div>

        {report.message && (
          <p role="status">{report.message}</p>
        )}

        <p className="method">
          Official filing links identify source documents.
          AXÍA does not mark document contents as verified until
          the document extraction and evidence pipeline has
          completed.
        </p>
      </section>

      <ReportGroup
        title="Annual Reports"
        description="Primary annual filings used for long-term fundamental and financial analysis."
        reports={annual}
      />

      <ReportGroup
        title="Quarterly Reports"
        description="Recent quarterly filings used to track changes in performance, balance-sheet position and operating trends."
        reports={quarterly}
      />

      <ReportGroup
        title="Current & Material Filings"
        description="Recent regulatory filings that may contain material company developments."
        reports={current}
      />

      {foreign.length > 0 && (
        <ReportGroup
          title="Foreign Issuer Reports"
          description="Verified regulatory filings submitted by foreign issuers."
          reports={foreign}
        />
      )}

      <section className="panel">
        <h3>Evidence & methodology</h3>

        <p>
          Report Intelligence currently provides verified issuer
          resolution, official filing discovery and decision-report
          selection. Document extraction, evidence-backed financial
          interpretation and report comparison are the next
          intelligence layers.
        </p>

        <Link href="/data-sources">
          Review AXÍA data methodology →
        </Link>
      </section>
    </div>
  );
}
