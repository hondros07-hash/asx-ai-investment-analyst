"use client";

import Link from "next/link";
import { FormEvent, useState } from "react";

const MARKETS = [
  { name: "Australia", flag: "🇦🇺" },
  { name: "United States", flag: "🇺🇸" },
  { name: "United Kingdom", flag: "🇬🇧" },
  { name: "Japan", flag: "🇯🇵" },
  { name: "Hong Kong", flag: "🇭🇰" },
  { name: "Canada", flag: "🇨🇦" },
] as const;

type MarketName = (typeof MARKETS)[number]["name"];

const MARKET_META: Record<
  MarketName,
  { benchmark: string; currency: string; gold: string }
> = {
  Australia: {
    benchmark: "S&P/ASX 200",
    currency: "AUD/USD",
    gold: "Gold (USD)",
  },
  "United States": {
    benchmark: "S&P 500",
    currency: "USD Index",
    gold: "Gold (USD)",
  },
  "United Kingdom": {
    benchmark: "FTSE 100",
    currency: "GBP/USD",
    gold: "Gold (USD)",
  },
  Japan: {
    benchmark: "Nikkei 225",
    currency: "USD/JPY",
    gold: "Gold (USD)",
  },
  "Hong Kong": {
    benchmark: "Hang Seng",
    currency: "USD/HKD",
    gold: "Gold (USD)",
  },
  Canada: {
    benchmark: "TSX Composite",
    currency: "USD/CAD",
    gold: "Gold (USD)",
  },
};

function EmptyValue() {
  return <span className="home-unavailable">—</span>;
}

function MarketCard({
  title,
  selected = false,
}: {
  title: string;
  selected?: boolean;
}) {
  return (
    <button
      type="button"
      className={`home-market-card${selected ? " selected" : ""}`}
    >
      <span>{title}</span>
      <strong><EmptyValue /></strong>
      <small>Data loading</small>
    </button>
  );
}

export function HomeDashboard() {
  const [market, setMarket] = useState<MarketName>("Australia");
  const [query, setQuery] = useState("");

  const meta = MARKET_META[market];

  function submitSearch(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();

    const ticker = query.trim().toUpperCase();
    if (!ticker) return;

    window.location.href = `/search?q=${encodeURIComponent(ticker)}`;
  }

  return (
    <div className="axia-home">
      <div className="home-top-strip">
        <form className="home-company-search" onSubmit={submitSearch}>
          <span className="home-search-icon">⌕</span>
          <input
            value={query}
            onChange={(event) => setQuery(event.target.value)}
            placeholder="Search any company, ETF or index (e.g. ZIP, QAN, AAPL, BHP) ..."
            aria-label="Search companies, ETFs and indices"
          />
        </form>

        <div className="home-country-nav" aria-label="Select market">
          {MARKETS.map((item) => (
            <button
              key={item.name}
              type="button"
              className={market === item.name ? "active" : ""}
              onClick={() => setMarket(item.name)}
            >
              <span className="home-country-flag">{item.flag}</span>
              <span>{item.name}</span>
            </button>
          ))}
        </div>
      </div>

      <section className="home-overview">
        <div className="home-overview-heading">
          <div>
            <h1>
              <span>
                {MARKETS.find((item) => item.name === market)?.flag}
              </span>
              Market Overview – {market}
            </h1>

            <p>
              Market status and verified quote timestamps will appear when the
              production market-data feed is connected.
            </p>
          </div>

          <blockquote>
            “The best investments are built on knowledge, not noise.”
            <small>— AXÍA</small>
          </blockquote>
        </div>

        <div className="home-headline-grid">
          <MarketCard title={meta.benchmark} selected />
          <MarketCard title="Secondary Index" />
          <MarketCard title="Market Index" />
          <MarketCard title={meta.currency} />
          <MarketCard title={meta.gold} />
        </div>

        <div className="home-primary-grid">
          <section className="home-widget home-chart-widget">
            <header>
              <strong>{meta.benchmark} Intraday Chart</strong>

              <nav aria-label="Chart range">
                <button type="button" className="active">1D</button>
                <button type="button">5D</button>
                <button type="button">1M</button>
                <button type="button">3M</button>
                <button type="button">1Y</button>
                <button type="button">5Y</button>
              </nav>
            </header>

            <div className="home-chart-empty">
              <div className="home-chart-grid" />
              <strong><EmptyValue /></strong>
              <p>Verified market series not connected yet.</p>
            </div>
          </section>

          <section className="home-widget">
            <header>
              <strong>{market === "Australia" ? "ASX" : market} Sectors</strong>
              <span>Awaiting verified data</span>
            </header>

            <div className="home-widget-tabs">
              <button className="active" type="button">Day</button>
              <button type="button">Week</button>
              <button type="button">Month</button>
              <button type="button">YTD</button>
            </div>

            <div className="home-empty-state">
              Sector performance will appear when the production market feed is
              connected.
            </div>
          </section>

          <section className="home-widget">
            <header>
              <strong>{market === "Australia" ? "ASX" : market} Indices</strong>
              <span>Awaiting verified data</span>
            </header>

            <div className="home-table-head">
              <span>Code</span>
              <span>Name</span>
              <span>Last</span>
              <span>% Chg</span>
            </div>

            <div className="home-empty-state">
              Verified index quotes are not currently available.
            </div>
          </section>
        </div>

        <div className="home-secondary-grid">
          <section className="home-widget">
            <header><strong>Top Gainers ({market})</strong></header>
            <div className="home-empty-state">
              No verified gainers loaded yet.
            </div>
          </section>

          <section className="home-widget">
            <header><strong>Biggest Fallers ({market})</strong></header>
            <div className="home-empty-state">
              No verified fallers loaded yet.
            </div>
          </section>

          <section className="home-widget">
            <header>
              <strong>Watchlist</strong>
              <span>My Watchlist</span>
            </header>
            <div className="home-empty-state">
              Your production watchlist is not connected yet.
            </div>
          </section>

          <section className="home-widget">
            <header>
              <strong>Volatility Index</strong>
              <span>{market}</span>
            </header>
            <div className="home-volatility">
              <strong><EmptyValue /></strong>
              <span>Unavailable</span>
            </div>
            <p className="home-widget-note">
              No substitute volatility index is shown when the correct
              market-specific benchmark is unavailable.
            </p>
          </section>
        </div>

        <div className="home-bottom-grid">
          <section className="home-widget">
            <header><strong>Upcoming Dividends ({market})</strong></header>
            <div className="home-empty-state">
              No verified forward dividend calendar connected yet. Undeclared
              dividends are never estimated.
            </div>
          </section>

          <section className="home-widget">
            <header><strong>Upcoming IPOs / Earnings ({market})</strong></header>
            <div className="home-empty-state">
              Verified calendar events will appear here.
            </div>
          </section>

          <section className="home-widget">
            <header>
              <strong>Global Markets</strong>
              <span>Market indices</span>
            </header>
            <div className="home-empty-state">
              Global index feeds will appear here after production connection.
            </div>
          </section>
        </div>

        <div className="home-research-cta">
          <div>
            <span className="eyebrow">AXÍA RESEARCH</span>
            <h2>From market context to company intelligence.</h2>
            <p>
              Search a listed company and continue into the Company Command
              Centre for fundamental, technical, filing, valuation and forecast
              research.
            </p>
          </div>

          <Link className="button" href="/search">
            Explore companies →
          </Link>
        </div>
      </section>
    </div>
  );
}
