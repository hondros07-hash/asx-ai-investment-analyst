"""AXÍA Our Mission — About-matched presentation, no market-data side effects."""
import streamlit as st

def render_our_mission():
    html = """<style>
    /* AXÍA V23.7.5.7 — reference-matched compact typography; overrides global heading margins. */
    .ax-mission{width:100%;margin:0 0 10px!important;padding:17px 24px 18px!important;background:#fff;border:1px solid #dbe6f0;border-radius:7px;color:#183b60;font-family:Arial,Helvetica,sans-serif}
    .ax-mission *{box-sizing:border-box}
    .ax-mission .eyebrow{color:#a67520!important;font-size:11px!important;line-height:1.35!important;font-weight:800!important;letter-spacing:.12em;text-transform:uppercase;margin:0 0 4px!important;padding:0!important}
    .ax-mission h1{font-size:19px!important;line-height:1.28!important;margin:3px 0 5px!important;padding:0!important;color:#122e4d!important;font-weight:750!important;letter-spacing:-.01em!important}
    .ax-mission h2{font-size:17px!important;line-height:1.32!important;margin:3px 0 5px!important;padding:0!important;color:#122e4d!important;font-weight:750!important}
    .ax-mission h3{font-size:14px!important;line-height:1.35!important;margin:5px 0 9px!important;color:#173b60!important;font-weight:750!important}
    .ax-mission p{font-size:12px!important;line-height:1.5!important;color:#455c76!important;margin:0 0 7px!important;padding:0!important}
    .ax-mission .hero{padding:0 0 10px!important;margin:0!important;background:transparent;border:0;border-bottom:1px solid #dce6f0;border-radius:0;color:#173d66}
    .ax-mission .hero p{max-width:100%}
    .ax-mission .greek{font-family:Georgia,serif;font-size:13px;color:#55718e;margin:0 0 7px}
    .ax-mission .section{padding:12px 0!important;margin:0!important;border-bottom:1px solid #dce6f0}
    .ax-mission .family{background:transparent;border:0;border-radius:0;padding:0!important}
    .ax-mission .cards{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:12px;margin-top:10px;align-items:stretch}
    .ax-mission .card{display:grid;grid-template-columns:42px minmax(0,1fr);gap:11px;background:#fff;border:1px solid #dbe6f0;border-radius:8px;padding:15px 14px;min-width:0}
    .ax-mission .card-icon{width:34px;height:34px;color:#a67520;margin-top:1px}
    .ax-mission .card-icon svg{display:block;width:34px;height:34px;fill:none;stroke:currentColor;stroke-width:1.8;stroke-linecap:round;stroke-linejoin:round}
    .ax-mission .number{font-size:11px;letter-spacing:.09em;font-weight:800;color:#a67520}
    .ax-mission .card p{font-size:11px;line-height:1.43;margin:0 0 7px}
    .ax-mission .card strong{color:#163e69}
    .ax-mission .closing{background:transparent;border:0;border-radius:0;padding:10px 0 0;margin-top:0}
    .ax-mission .closing h2{margin:3px 0 4px}
    .ax-mission .fine{font-size:10px;line-height:1.45;color:#657a91}
    @media(max-width:1000px){.ax-mission .cards{grid-template-columns:1fr}.ax-mission .card{grid-template-columns:42px minmax(0,1fr)}}
    @media(max-width:650px){.ax-mission{padding:16px}.ax-mission .section{padding:14px 0}.ax-mission .card{padding:14px}}
    </style><div class="ax-mission">
    <section class="hero"><div class="eyebrow">Our mission · Our purpose</div>
    <h1>All the evidence. A clearer perspective.</h1>
    <p>Our mission is to bring fragmented financial information together into one trusted investment research platform, helping investors understand what matters, evaluate the evidence and make informed decisions with greater clarity and confidence.</p></section>
    <section class="section"><div class="eyebrow">Why we exist</div><h2>Clarity in a world of financial noise.</h2>
    <p>Research is scattered across market-data services, financial statements, company announcements, news, charting tools, valuation models and portfolio trackers. AXÍA aims to connect this information in one calm, coherent research workspace.</p>
    <p>Our purpose is not to add more noise. It is to help investors understand how evidence connects to business performance, valuation and the assumptions behind an investment thesis.</p></section>
    <section class="section"><div class="eyebrow">Our philosophy</div><h2>20% experience. 80% intelligence.</h2>
    <p>The website makes research accessible. The intelligence behind it does the problem-solving: verifying data, connecting evidence, analysing companies, testing valuations and monitoring the reasons behind investment decisions.</p>
    <p>We build the intelligence first, then design the interface that communicates it. The value lies not in how much information AXÍA displays, but in the problems it helps investors solve.</p></section>
    <section class="section"><div class="eyebrow">What guides us</div><h2>Our three core principles</h2>
    <div class="cards">
    <article class="card"><div class="card-icon" aria-hidden="true"><svg viewBox="0 0 36 36"><circle cx="18" cy="9" r="5"/><circle cx="7" cy="14" r="3"/><circle cx="29" cy="14" r="3"/><path d="M9 30v-5c0-5 4-8 9-8s9 3 9 8v5zM2 30v-6c0-3 2-5 5-5M34 30v-6c0-3-2-5-5-5"/></svg></div><div class="card-body"><div class="number">01 / CLARITY</div><h3>Respect your time.</h3><p><strong>Less searching. Less distraction.</strong> Bring relevant financial information into one connected view, with important findings first and supporting detail available when needed.</p><p>Focus on developments that materially affect a company and the investor's research thesis.</p></div></article>
    <article class="card"><div class="card-icon" aria-hidden="true"><svg viewBox="0 0 36 36"><path d="M7 3h14l6 6v8M21 3v7h6M7 3v29h14M12 15h10M12 20h8"/><circle cx="25" cy="24" r="6"/><path d="m29.5 28.5 5 5"/></svg></div><div class="card-body"><div class="number">02 / EVIDENCE</div><h3>Respect the facts.</h3><p><strong>Trust begins with traceable information.</strong> Distinguish reported figures from forecasts, estimates, derived calculations and AI interpretation.</p><p>Important figures should show their source, reporting period and methodology. Missing or unverified data must not be silently invented.</p></div></article>
    <article class="card"><div class="card-icon" aria-hidden="true"><svg viewBox="0 0 36 36"><path d="M5 31V22h5v9M15 31V17h5v14M25 31V11h5v20M4 17l10-8 7 5 11-11M26 3h6v6"/></svg></div><div class="card-body"><div class="number">03 / INTELLIGENCE</div><h3>Make the reasoning visible.</h3><p><strong>Analysis should be inspectable.</strong> Connect company performance, valuation, risks and market developments through explicit assumptions and calculations.</p><p>Monitor whether new evidence supports or challenges an investment thesis, without presenting modelled outcomes as certainties.</p></div></article>
    </div></section>
    <section class="closing"><div class="eyebrow">Our commitment</div><h2>Built to inform your judgment. Not replace it.</h2>
    <p>AXÍA exists to help investors ask better questions, understand what drives a business and monitor whether their investment thesis still holds. Your decisions remain your own.</p>
    <p class="fine">AXÍA provides research and information, not personal financial advice. Data, models and AI-generated analysis can contain errors, delays or omissions. Verify important information against primary sources and seek appropriately licensed professional advice where needed.</p></section>
    </div>"""
    # Strip indentation before Markdown parsing: four leading spaces make HTML a code block.
    st.markdown("".join(line.lstrip() for line in html.splitlines()), unsafe_allow_html=True)
