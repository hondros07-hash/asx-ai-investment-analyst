"use client";

import { useEffect, useState } from "react";

type CompanyLogoProps = {
  ticker: string;
  name?: string;
  size?: number;
  className?: string;
};

type CompanyIdentity = {
  ticker?: string;
  domain?: string | null;
};

function initialsFor(ticker: string, name?: string) {
  const cleanTicker = ticker.split(".")[0].replace(/[^A-Z0-9]/gi, "");

  if (cleanTicker) {
    return cleanTicker.slice(0, 2).toUpperCase();
  }

  return (name || "?").slice(0, 2).toUpperCase();
}

export function CompanyLogo({
  ticker,
  name,
  size = 32,
  className = "",
}: CompanyLogoProps) {
  const clientId = process.env.NEXT_PUBLIC_BRANDFETCH_CLIENT_ID;
  const [domain, setDomain] = useState<string | null>(null);
  const [domainResolved, setDomainResolved] = useState(false);
  const [domainLogoFailed, setDomainLogoFailed] = useState(false);
  const [tickerLogoFailed, setTickerLogoFailed] = useState(false);

  const symbol = ticker.trim();
  const initials = initialsFor(ticker, name);

  useEffect(() => {
    const controller = new AbortController();

    setDomain(null);
    setDomainResolved(false);
    setDomainLogoFailed(false);
    setTickerLogoFailed(false);

    if (!symbol) {
      setDomainResolved(true);
      return () => controller.abort();
    }

    fetch(`/api/company-identity/${encodeURIComponent(symbol)}`, {
      signal: controller.signal,
    })
      .then((response) => {
        if (!response.ok) {
          throw new Error("Identity unavailable");
        }
        return response.json() as Promise<CompanyIdentity>;
      })
      .then((identity) => {
        setDomain(identity.domain?.trim() || null);
      })
      .catch((error: unknown) => {
        if (
          !(error instanceof DOMException && error.name === "AbortError")
        ) {
          setDomain(null);
        }
      })
      .finally(() => {
        if (!controller.signal.aborted) {
          setDomainResolved(true);
        }
      });

    return () => controller.abort();
  }, [symbol]);

  const identifier =
    domainResolved && domain && !domainLogoFailed ? domain : symbol;

  const logoUrl =
    clientId &&
    identifier &&
    !(identifier === symbol && tickerLogoFailed)
      ? `https://cdn.brandfetch.io/${encodeURIComponent(identifier)}/w/${size * 2}/h/${size * 2}/icon?c=${encodeURIComponent(clientId)}`
      : null;

  if (!logoUrl) {
    return (
      <span
        className={`axia-company-logo axia-company-logo-fallback ${className}`}
        style={{ width: size, height: size }}
        aria-hidden="true"
      >
        {initials}
      </span>
    );
  }

  return (
    <span
      className={`axia-company-logo ${className}`}
      style={{ width: size, height: size }}
    >
      <img
        src={logoUrl}
        alt=""
        width={size}
        height={size}
        loading="lazy"
        onError={() => {
          if (domainResolved && domain && identifier === domain) {
            setDomainLogoFailed(true);
          } else {
            setTickerLogoFailed(true);
          }
        }}
      />
    </span>
  );
}
