# V18.3 — Dynamic Company Branding

Adds dynamic branding for the company currently being researched.

Company header:
- derives the brand icon from the company's current website when available
- requests a higher-resolution current website icon
- falls back to provider logo metadata, then the existing initials tile

Browser tab:
- title changes to: `Company Name (Ticker) | Market Investment Analyst`
- favicon changes to the selected company's current brand icon when available
- changing companies updates the tab on Streamlit rerun

Examples:
- `Zip Co Limited (ZIP) | Market Investment Analyst`
- `The Coca-Cola Company (KO) | Market Investment Analyst`

The initial generic page configuration remains as a safe startup fallback.

Deployment diagnostic:
V18.3 • Market Investment Analyst • dynamic company branding
