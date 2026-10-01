from __future__ import annotations

import html
import os
import re
from dataclasses import dataclass
from typing import Any
from urllib.parse import urlparse
from urllib.request import Request, urlopen


SEC_HOSTS = {"sec.gov", "www.sec.gov"}

DEFAULT_TIMEOUT = 20
MAX_DOCUMENT_BYTES = 15_000_000


@dataclass(frozen=True)
class ExtractedDocument:
    status: str
    source: str
    document_url: str
    issuer_verified: bool
    document_verified: bool
    content_type: str | None
    text: str | None
    text_length: int
    error: str | None = None


def _sec_user_agent() -> str:
    return os.environ.get(
        "AXIA_SEC_USER_AGENT",
        "AXIA Research research@axiaindex.com",
    )


def _is_official_sec_url(url: str) -> bool:
    try:
        parsed = urlparse(url)
    except Exception:
        return False

    return (
        parsed.scheme == "https"
        and parsed.hostname in SEC_HOSTS
        and parsed.path.startswith("/Archives/")
    )
def _fetch_sec_document(url: str) -> tuple[bytes, str | None]:
    if not _is_official_sec_url(url):
        raise ValueError("Document URL is not an official SEC Archives URL.")

    request = Request(
        url,
        headers={
            "User-Agent": _sec_user_agent(),
            "Accept-Encoding": "identity",
            "Accept": "text/html,application/xhtml+xml,text/plain",
        },
    )

    with urlopen(request, timeout=DEFAULT_TIMEOUT) as response:
        final_url = response.geturl()

        if not _is_official_sec_url(final_url):
            raise ValueError("SEC request redirected to an unapproved URL.")

        content_type = response.headers.get_content_type()

        content_length = response.headers.get("Content-Length")
        if content_length:
            try:
                if int(content_length) > MAX_DOCUMENT_BYTES:
                    raise ValueError("SEC document exceeds AXIA extraction size limit.")
            except ValueError as exc:
                if "exceeds" in str(exc):
                    raise

        raw = response.read(MAX_DOCUMENT_BYTES + 1)

        if len(raw) > MAX_DOCUMENT_BYTES:
            raise ValueError("SEC document exceeds AXIA extraction size limit.")

        if not raw:
            raise ValueError("SEC returned an empty document.")

        return raw, content_type

def _html_to_text(raw: bytes) -> str:
    decoded = raw.decode("utf-8", errors="replace")

    decoded = re.sub(
        r"(?is)<(script|style|noscript).*?>.*?</\1>",
        " ",
        decoded,
    )

    decoded = re.sub(r"(?i)<br\s*/?>", "\n", decoded)
    decoded = re.sub(r"(?i)</(p|div|tr|li|h[1-6])>", "\n", decoded)
    decoded = re.sub(r"(?s)<[^>]+>", " ", decoded)

    decoded = html.unescape(decoded)
    decoded = decoded.replace("\xa0", " ")

    lines: list[str] = []

    for line in decoded.splitlines():
        cleaned = re.sub(r"[ \t]+", " ", line).strip()

        if cleaned:
            lines.append(cleaned)

    text = "\n".join(lines)
    text = re.sub(r"\n{3,}", "\n\n", text)

    return text.strip()


def _extract_text(raw: bytes, content_type: str | None) -> str:
    allowed_types = {
        "text/html",
        "application/xhtml+xml",
        "text/plain",
    }

    if content_type and content_type not in allowed_types:
        raise ValueError(
            f"Unsupported SEC document content type: {content_type}"
        )

    if content_type == "text/plain":
        text = raw.decode("utf-8", errors="replace").strip()
    else:
        text = _html_to_text(raw)

    if len(text) < 100:
        raise ValueError(
            "SEC document did not contain enough extractable text."
        )

    return text

def extract_official_sec_document(
    document_url: str,
    *,
    issuer_verified: bool,
) -> ExtractedDocument:
    if not issuer_verified:
        return ExtractedDocument(
            status="unavailable",
            source="SEC EDGAR",
            document_url=document_url,
            issuer_verified=False,
            document_verified=False,
            content_type=None,
            text=None,
            text_length=0,
            error="Issuer identity has not been verified.",
        )

    if not _is_official_sec_url(document_url):
        return ExtractedDocument(
            status="unavailable",
            source="SEC EDGAR",
            document_url=document_url,
            issuer_verified=True,
            document_verified=False,
            content_type=None,
            text=None,
            text_length=0,
            error="Document URL is not an approved SEC Archives URL.",
        )

    try:
        raw, content_type = _fetch_sec_document(document_url)
        extracted_text = _extract_text(raw, content_type)
        text = _clean_filing_text(extracted_text)

        return ExtractedDocument(
            status="extracted",
            source="SEC EDGAR",
            document_url=document_url,
            issuer_verified=True,
            document_verified=False,
            content_type=content_type,
            text=text,
            text_length=len(text),
            error=None,
        )

    except Exception as exc:
        return ExtractedDocument(
            status="unavailable",
            source="SEC EDGAR",
            document_url=document_url,
            issuer_verified=True,
            document_verified=False,
            content_type=None,
            text=None,
            text_length=0,
            error=f"{type(exc).__name__}: {exc}",
        )

def _clean_filing_text(text: str) -> str:
    if not text:
        return ""

    lines = text.splitlines()
    cleaned_lines: list[str] = []

    taxonomy_pattern = re.compile(
        r"(https?://(?:www\.)?(?:fasb\.org|xbrl\.org)/"
        r"|us-gaap/"
        r"|dei/"
        r"|country/"
        r"|currency/)",
        re.IGNORECASE,
    )

    for line in lines:
        cleaned = line.strip()

        if not cleaned:
            continue

        # Remove lines dominated by XBRL taxonomy / namespace metadata.
        taxonomy_hits = len(taxonomy_pattern.findall(cleaned))

        if taxonomy_hits >= 2:
            continue

        # Remove extremely long metadata-style lines containing taxonomy URLs.
        if len(cleaned) > 500 and taxonomy_pattern.search(cleaned):
            continue

        cleaned_lines.append(cleaned)

    result = "\n".join(cleaned_lines)
    result = re.sub(r"\n{3,}", "\n\n", result)

    return result.strip()
