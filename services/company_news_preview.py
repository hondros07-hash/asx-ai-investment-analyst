"""AXÍA V23.7.25: conservative company-news preview filtering.

Do not treat provider's Company layer as proof that an article concerns the issuer.
Ambiguous headlines are omitted rather than mislabelled as company-specific.
"""
import re
from difflib import SequenceMatcher
from datetime import timedelta
from urllib.parse import urlparse
import pandas as pd

GENERIC = ("undervalued small caps", "insider activity", "insider action",
           "stocks to watch", "top stocks", "best stocks", "stock picks",
           "asian small caps", "market roundup", "market wrap")
STOP = {"limited", "ltd", "inc", "corp", "corporation", "company", "co", "group",
        "holdings", "plc", "the", "class", "ordinary", "shares"}

def _words(s):
    return re.findall(r"[a-z0-9]+", str(s or "").lower())

def _identity_terms(ticker, name):
    base = str(ticker or "").upper().split(".")[0]
    words = [w for w in _words(name) if w not in STOP]
    terms = {base.lower(), " ".join(words)}
    if len(words) > 1:
        terms.add(" ".join(words[:2]))
    # Very short brand names alone are ambiguous; require an exact word boundary.
    if words and len(words[0]) >= 4:
        terms.add(words[0])
    return {t for t in terms if len(t) >= 3}

def _relevant(headline, ticker, name):
    text = " ".join(_words(headline))
    terms = _identity_terms(ticker, name)
    return any(re.search(r"(?<![a-z0-9])" + re.escape(t) + r"(?![a-z0-9])", text)
               for t in terms)

def clean_company_news(df, ticker, name, limit=5):
    if df is None or df.empty:
        return pd.DataFrame(columns=["Date", "Headline", "Source", "URL", "Published", "Related Coverage"])
    kept = []
    for _, row in df.iterrows():
        title = str(row.get("Headline") or "").strip()
        url = str(row.get("URL") or "").strip()
        if not title or not _relevant(title, ticker, name):
            continue
        if any(term in title.lower() for term in GENERIC) and not _relevant(title, ticker, name):
            continue
        if urlparse(url).scheme not in ("http", "https"):
            continue
        published = pd.to_datetime(row.get("Published"), utc=True, errors="coerce")
        normalized = " ".join(w for w in _words(title) if w not in STOP)
        duplicate = None
        for old in kept:
            other = old["_published"]
            if pd.notna(published) and pd.notna(other) and abs(published-other) > timedelta(hours=72):
                continue
            if SequenceMatcher(None, normalized, old["_normalized"]).ratio() >= .80:
                duplicate = old
                break
        if duplicate is not None:
            duplicate["Related Coverage"] += 1
            continue
        item = row.to_dict()
        item["Related Coverage"] = 0
        item["_published"] = published
        item["_normalized"] = normalized
        kept.append(item)
    kept.sort(key=lambda x: x["_published"] if pd.notna(x["_published"]) else pd.Timestamp.min.tz_localize("UTC"), reverse=True)
    result = pd.DataFrame(kept[:max(1, min(int(limit), 10))])
    return result.drop(columns=["_published", "_normalized"], errors="ignore")
