"use client";
import "../app/home-reference.css";
import Link from "next/link";
import {usePathname} from "next/navigation";
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

export function HomeReferenceShell({ children }: { children: React.ReactNode }) {
  const path = usePathname();

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
            {homeNavigation.map((item) => (
              <Link
                key={item.title}
                href={item.href}
                className={
                  path === item.href ||
                  (item.href !== "/" && path.startsWith(item.href))
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
            ))}
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
