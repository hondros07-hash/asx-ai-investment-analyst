# V14.1 — Announcements Hotfix

Fixes the ASX Announcements & Reports crash shown for ZIP.AX.

Cause:
The ASX public fallback can legitimately return an empty pandas DataFrame with no columns.
The V13/V14 normalization code then attempted `p["URL"]`, causing `KeyError: 'URL'`.

Fix:
- Empty provider/fallback results now return a normalized empty announcement schema.
- URL/PDFURL/ReadURL fields are only derived after validating the frame.
- Has PDF is derived from an actual PDF URL instead of blindly assuming every fallback row is a PDF.
- V14 Technical Analysis Lab remains included unchanged.

This prevents the page from crashing. It does not turn the public ASX fallback into a complete ComNews feed.
