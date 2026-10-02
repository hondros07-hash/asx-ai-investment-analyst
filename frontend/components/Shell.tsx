"use client";
import "../app/home-reference.css";
import Link from "next/link";
import {usePathname} from "next/navigation";
import {useEffect, useState} from "react";
const companySections = [
  { title: "Overview", slug: "overview", icon: "▦" },
  { title: "Fundamentals", slug: "fundamentals", icon: "▥" },
  { title: "Technical", slug: "technical", icon: "⌁" },
  { title: "Announcements & Reports", slug: "announcements", icon: "▤" },
  { title: "Report Intelligence", slug: "report-intelligence", icon: "◉" },
  { title: "News", slug: "news", icon: "▧" },
  { title: "Thesis Scorecard", slug: "thesis", icon: "☑" },
  { title: "Catalyst Calendar", slug: "catalysts", icon: "▦" },
  { title: "Quant", slug: "quant", icon: "⌘" },
  { title: "Forecasts", slug: "forecasts", icon: "◇" },
  { title: "Finance", slug: "finance", icon: "▥" },
];

const homeNavigation = [
  { title: "Home", subtitle: "Global Market Overview", href: "/", icon: "⌂" },
  { title: "Company Search", subtitle: "Find & Analyse Stocks", href: "/search", icon: "⌕" },
  { title: "Company Command Centre", subtitle: "Deep Analysis & Reports", href: "/search", icon: "▣" },
  { title: "Markets", subtitle: "Indices, Sectors & Heatmaps", href: "/markets", icon: "◫" },
  { title: "Watchlist", subtitle: "Track Your Stocks", href: "/watchlist", icon: "☆" },
  { title: "Portfolio", subtitle: "Performance & Analytics", href: "/portfolio", icon: "▥" },
  { title: "Screening", subtitle: "Find Opportunities", href: "/screening", icon: "⌁" },
  { title: "Alerts", subtitle: "Price & News Alerts", href: "/alerts", icon: "♢" },
  { title: "Calendar", subtitle: "Dividends, Earnings & IPOs", href: "/calendar", icon: "□" },
  { title: "Research Tools", subtitle: "Valuation, Forecasts & Scores", href: "/research-tools", icon: "⌘" },
  { title: "Settings", subtitle: "Preferences", href: "/settings", icon: "⚙" },
];

export function Shell({ children, ticker }: { children: React.ReactNode; ticker?: string }) {
  const path = usePathname();
  const isCompanyPath = Boolean(ticker) && path.startsWith("/company/");
  const [cccOpen, setCccOpen] = useState(isCompanyPath);

  useEffect(() => {
    if (isCompanyPath) setCccOpen(true);
  }, [isCompanyPath]);

  const navigation = homeNavigation.map((item) =>
    item.title === "Company Command Centre"
      ? {
          ...item,
          href: ticker
            ? `/company/${encodeURIComponent(ticker)}/overview`
            : "/search",
        }
      : item
  );

  return (
    <div className="home-reference-shell">
      <header className="home-reference-banner">
        <div className="home-reference-brand">
          <strong>AXÍA</strong>
          <span>Market Investment Analyst</span>
          <small>Global Markets. Smarter Decisions.</small>
        </div>

        <div className="home-reference-motto">
          <blockquote>“A calm mind<br />builds a wealthy future.”</blockquote>
          <span>DISCIPLINE&nbsp;&nbsp;|&nbsp;&nbsp;ANALYSIS&nbsp;&nbsp;|&nbsp;&nbsp;OPPORTUNITY</span>
        </div>
      </header>

      <div className="home-reference-workspace">
        <aside className="home-reference-sidebar">
          <nav aria-label="AXÍA navigation">
            {navigation.map((item) => {
              const isCompanyCommandCentre = item.title === "Company Command Centre";
              const isActive = isCompanyCommandCentre
                ? isCompanyPath
                : path === item.href ||
                  (item.href !== "/" && path.startsWith(item.href));

              return (
                <div key={item.title}>
                  {isCompanyCommandCentre ? (
                    <button
                      type="button"
                      className={
                        isActive
                          ? "home-reference-nav home-reference-ccc-toggle active"
                          : "home-reference-nav home-reference-ccc-toggle"
                      }
                      onClick={() => setCccOpen((open) => !open)}
                      aria-expanded={cccOpen}
                      aria-controls="axia-ccc-sections"
                    >
                      <span className="home-reference-nav-icon">{item.icon}</span>
                      <span className="home-reference-nav-copy">
                        <strong>{item.title}</strong>
                        <small>{item.subtitle}</small>
                      </span>
                      <span
                        className={
                          cccOpen
                            ? "home-reference-ccc-chevron open"
                            : "home-reference-ccc-chevron"
                        }
                        aria-hidden="true"
                      >
                        ▾
                      </span>
                    </button>
                  ) : (
                    <Link
                      href={item.href}
                      className={
                        isActive
                          ? "home-reference-nav active"
                          : "home-reference-nav"
                      }
                    >
                      <span className="home-reference-nav-icon">{item.icon}</span>
                      <span className="home-reference-nav-copy">
                        <strong>{item.title}</strong>
                        <small>{item.subtitle}</small>
                      </span>
                    </Link>
                  )}

                  {isCompanyCommandCentre && cccOpen && (
                    <div
                      id="axia-ccc-sections"
                      className="home-reference-ccc-nav"
                      aria-label="Company Command Centre sections"
                    >
                      {ticker ? (
                        companySections.map((section) => {
                          const href = `/company/${encodeURIComponent(ticker)}/${section.slug}`;
                          const selected = path === href;

                          return (
                            <Link
                              key={section.slug}
                              href={href}
                              className={
                                selected
                                  ? "home-reference-ccc-link active"
                                  : "home-reference-ccc-link"
                              }
                              aria-current={selected ? "page" : undefined}
                            >
                              <span className="home-reference-ccc-icon">
                                {section.icon}
                              </span>
                              <span>{section.title}</span>
                            </Link>
                          );
                        })
                      ) : (
                        <Link
                          href="/search"
                          className="home-reference-ccc-link home-reference-ccc-select"
                        >
                          <span className="home-reference-ccc-icon">⌕</span>
                          <span>Select a company first</span>
                        </Link>
                      )}
                    </div>
                  )}
                </div>
              );
            })}
          </nav>

          <div className="home-reference-wealth">
            <span className="home-reference-column">♜</span>
            <strong>KNOWLEDGE COMPOUNDS WEALTH</strong>
          </div>

          <div className="home-reference-copyright">
            © 2026 Axia. All rights reserved.
          </div>
        </aside>

        <div className="home-reference-content">
          <main>{children}</main>
        </div>
      </div>
    </div>
  );
}
