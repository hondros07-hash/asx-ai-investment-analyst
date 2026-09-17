# Chrímata V20.0.1 — Persistent Terminal Shell

This build corrects the V20.0.0 shell issues seen after deployment.

- Chrímata panoramic masthead now renders on every workspace page, not only Home.
- Header artwork is pre-scaled/sharpened for a 1536px desktop viewport and displayed without the previous dark overlay/filter.
- Main Streamlit canvas explicitly reserves the sidebar width using current `stMain` selectors plus legacy fallbacks.
- Sidebar remains below the masthead and no longer intentionally overlays the dashboard canvas.
- Main content starts immediately below the masthead with reduced whitespace.
- Home cards/tables receive a tighter white/navy terminal treatment while existing live-data and research engines remain intact.
- Python cache/build artefacts remain excluded by `.gitignore`.

Deployment: replace the contents of the local Git repository with this package, commit to `main`, then push origin.
