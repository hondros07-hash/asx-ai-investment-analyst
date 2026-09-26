"""AXÍA V23.7.5 — About Us. Presentation only; no market-data or navigation side effects."""
import streamlit as st

def render_about_us():
    html = """<style>
    /* AXÍA V23.7.5.5 — screenshot-matched About, isolated from global UI. */
    .ax-about{width:100%;margin:0 0 10px;padding:17px 24px 18px;background:#fff;border:1px solid #dbe6f0;border-radius:7px;color:#183b60;font-family:Arial,Helvetica,sans-serif}
    .ax-about *{box-sizing:border-box}
    .ax-about .eyebrow{color:#a67520!important;font-size:11px;font-weight:800;letter-spacing:.12em;text-transform:uppercase}
    .ax-about h1{font-size:19px;line-height:1.28;margin:5px 0 6px;color:#122e4d!important;font-weight:750;letter-spacing:-.01em}
    .ax-about h2{font-size:17px;line-height:1.32;margin:5px 0 7px;color:#122e4d!important;font-weight:750}
    .ax-about h3{font-size:14px;line-height:1.35;margin:5px 0 9px;color:#173b60!important;font-weight:750}
    .ax-about p{font-size:12px;line-height:1.5;color:#455c76;margin:0 0 7px}
    .ax-about .hero{padding:0 0 10px;background:transparent;border:0;border-bottom:1px solid #dce6f0;border-radius:0;color:#173d66}
    .ax-about .hero p{max-width:100%}
    .ax-about .greek{font-family:Georgia,serif;font-size:13px;color:#55718e;margin:0 0 7px}
    .ax-about .section{padding:12px 0;border-bottom:1px solid #dce6f0}
    .ax-about .family{background:transparent;border:0;border-radius:0;padding:0}
    .ax-about .cards{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:12px;margin-top:10px;align-items:stretch}
    .ax-about .card{display:grid;grid-template-columns:42px minmax(0,1fr);gap:11px;background:#fff;border:1px solid #dbe6f0;border-radius:8px;padding:15px 14px;min-width:0}
    .ax-about .card-icon{width:34px;height:34px;color:#a67520;margin-top:1px}
    .ax-about .card-icon svg{display:block;width:34px;height:34px;fill:none;stroke:currentColor;stroke-width:1.8;stroke-linecap:round;stroke-linejoin:round}
    .ax-about .number{font-size:11px;letter-spacing:.09em;font-weight:800;color:#a67520}
    .ax-about .card p{font-size:11px;line-height:1.43;margin:0 0 7px}
    .ax-about .card strong{color:#163e69}
    .ax-about .closing{background:transparent;border:0;border-radius:0;padding:10px 0 0;margin-top:0}
    .ax-about .closing h2{margin:3px 0 4px}
    .ax-about .fine{font-size:10px;line-height:1.45;color:#657a91}
    @media(max-width:1000px){.ax-about .cards{grid-template-columns:1fr}.ax-about .card{grid-template-columns:42px minmax(0,1fr)}}
    @media(max-width:650px){.ax-about{padding:16px}.ax-about .section{padding:14px 0}.ax-about .card{padding:14px}}
    </style><div class="ax-about">
    <section class="hero"><div class="eyebrow" style="color:#a67520">Our story · Our purpose</div>
    <h1>Welcome to Axía. We are here to serve you.</h1>
    <p>The name Axía derives from the classical Greek word <em>axios</em> (ἄξιος), meaning worthy or deserving, and <em>axía</em> (αξία), meaning value.<br>It reflects what we seek in financial research: a clearer understanding of intrinsic value.</p></section>
    <section class="section"><div class="eyebrow">Why we exist</div><h2>Clarity in a world of financial noise.</h2>
    <p>Axía was created to go beyond a generic market tracker or an AI summary of headlines. Investors face information overload, inconsistent data and models whose assumptions are difficult to inspect. We aim to bring the evidence together in one calm, coherent research workspace.</p>
    <p>Our philosophy brings Greek cultural values together with disciplined financial analysis, transparent calculations and technology designed to support independent judgement.</p></section>
    <section class="section"><div class="family"><div class="eyebrow">Our cultural anchor</div><h2>Oikogéneia · οικογένεια</h2>
    <p>In Greek culture, family is a lasting commitment to care, trust and stewardship across generations. It is the foundation of our approach to the people who use Axía.</p>
    <p>We see subscribers as people making decisions that affect their lives and the people who matter to them—not merely entries in a database. Our responsibility is to present useful evidence clearly, acknowledge uncertainty and help them research with greater confidence, without making their decisions for them.</p></div></section>
    <section class="section"><div class="eyebrow">What guides us</div><h2>Our three core principles</h2>
    <div class="cards">
    <article class="card"><div class="card-icon" aria-hidden="true"><svg viewBox="0 0 36 36"><circle cx="18" cy="9" r="5"/><circle cx="7" cy="14" r="3"/><circle cx="29" cy="14" r="3"/><path d="M9 30v-5c0-5 4-8 9-8s9 3 9 8v5zM2 30v-6c0-3 2-5 5-5M34 30v-6c0-3-2-5-5-5"/></svg></div><div class="card-body"><div class="number">01 / VALUE</div><h3>Respect your time.</h3><p><strong>We value our subscribers like family.</strong> Research should clarify rather than overwhelm. Axía brings market developments, company fundamentals and relevant signals into a coherent view.</p><p>Our causal synthesis architecture is designed to connect events to potential business transmission channels, including affected operating metrics and margin drivers. These are analytical interpretations, not certainties.</p></div></article>
    <article class="card"><div class="card-icon" aria-hidden="true"><svg viewBox="0 0 36 36"><path d="M7 3h14l6 6v8M21 3v7h6M7 3v29h14M12 15h10M12 20h8"/><circle cx="25" cy="24" r="6"/><path d="m29.5 28.5 5 5"/></svg></div><div class="card-body"><div class="number">02 / WORTH</div><h3>Respect the evidence.</h3><p><strong>Trust begins with honest data.</strong> We aim to prioritise traceable company information and distinguish reported figures from estimates and derived calculations.</p><p>Where provider data is incomplete, statement-recovery workflows can use available filings and calculate metrics such as free cash flow (operating cash flow less capital expenditure). Missing or unverified information should be identified, never silently invented.</p></div></article>
    <article class="card"><div class="card-icon" aria-hidden="true"><svg viewBox="0 0 36 36"><path d="M5 31V22h5v9M15 31V17h5v14M25 31V11h5v20M4 17l10-8 7 5 11-11M26 3h6v6"/></svg></div><div class="card-body"><div class="number">03 / MERIT</div><h3>Make the reasoning visible.</h3><p><strong>An investment thesis should earn its place through evidence.</strong> Models need assumptions, limitations and calculations that can be examined and challenged.</p><p>Our research architecture works toward clear source attribution, calculation lineage and validation indicators for metrics, forecasts and scenarios. AI-assisted interpretation is kept distinct from deterministic arithmetic and reported facts.</p></div></article>
    </div></section>
    <section class="closing"><div class="eyebrow">Our commitment</div><h2>All the evidence. A clearer perspective.</h2>
    <p>Axía exists to help you ask better questions, understand what drives a business and monitor whether the reasons behind an investment still hold. Your decisions remain your own.</p>
    <p class="fine">Axía provides research and information, not personal financial advice. Data, models and AI-generated analysis can contain errors, delays or omissions. Verify important information against primary sources and seek appropriately licensed professional advice where needed.</p></section>
    </div>"""
    # Strip indentation before Markdown parsing: four leading spaces make HTML a code block.
    st.markdown("".join(line.lstrip() for line in html.splitlines()), unsafe_allow_html=True)
