"""AXÍA V23.7.5 — About Us. Presentation only; no market-data or navigation side effects."""
import streamlit as st

def render_about_us():
    st.markdown("""<style>
    .ax-about{max-width:1120px;margin:0 auto 24px;color:#12365c;font-family:Arial,Helvetica,sans-serif}
    .ax-about *{box-sizing:border-box}.ax-about .eyebrow{color:#1871bf;font-size:11px;font-weight:800;letter-spacing:.16em;text-transform:uppercase}
    .ax-about h1{font-size:clamp(30px,4vw,48px);line-height:1.12;letter-spacing:-.035em;margin:12px 0 18px;color:#082f5b}
    .ax-about h2{font-size:clamp(23px,3vw,31px);letter-spacing:-.025em;color:#082f5b;margin:0 0 15px}
    .ax-about h3{font-size:21px;color:#082f5b;margin:8px 0 12px}.ax-about p{font-size:15px;line-height:1.8;color:#4b617b;margin:0 0 15px}
    .ax-about .hero{padding:48px clamp(24px,5vw,62px);background:linear-gradient(120deg,#082f5b,#125c9b);border-radius:16px;color:#fff}
    .ax-about .hero h1,.ax-about .hero p{color:#fff}.ax-about .hero p{max-width:780px;color:#e0ebf7}
    .ax-about .greek{font-family:Georgia,serif;font-size:20px;color:#9acdf7;margin:0 0 10px}
    .ax-about .section{padding:42px 0;border-bottom:1px solid #dce7f2}.ax-about .section:last-child{border-bottom:0}
    .ax-about .family{background:#fff;border:1px solid #dce7f2;border-radius:14px;padding:32px}
    .ax-about .cards{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:18px;margin-top:24px}
    .ax-about .card{background:#fff;border:1px solid #dce7f2;border-radius:13px;padding:26px;min-width:0;border-top:4px solid #1871bf}
    .ax-about .number{font-size:12px;letter-spacing:.13em;font-weight:800;color:#1871bf}
    .ax-about .card p{font-size:14px;line-height:1.75}.ax-about .card strong{color:#163e69}
    .ax-about .closing{background:#edf5fc;border-radius:14px;padding:30px;margin-top:30px}
    .ax-about .fine{font-size:12px;line-height:1.6;color:#60758e}
    @media(max-width:850px){.ax-about .cards{grid-template-columns:1fr}.ax-about .hero{padding:30px 24px}.ax-about .section{padding:26px 0}.ax-about .family{padding:23px}}
    </style><div class="ax-about">
    <section class="hero"><div class="eyebrow" style="color:#a6d6ff">Our story · Our purpose</div>
    <h1>The Axía Story</h1><div class="greek">Αξία · Worth. Value. Merit.</div>
    <p>Welcome to Axía. We are here to serve you.</p>
    <p>Our name draws on the Greek words <em>axios</em> (ἄξιος), meaning worthy or deserving, and <em>axía</em> (αξία), meaning value. It reflects what we seek in financial research: a clearer understanding of intrinsic value.</p></section>
    <section class="section"><div class="eyebrow">Why we exist</div><h2>Clarity in a world of financial noise.</h2>
    <p>Axía was created to go beyond a generic market tracker or an AI summary of headlines. Investors face information overload, inconsistent data and models whose assumptions are difficult to inspect. We aim to bring the evidence together in one calm, coherent research workspace.</p>
    <p>Our philosophy brings Greek cultural values together with disciplined financial analysis, transparent calculations and technology designed to support independent judgement.</p></section>
    <section class="section"><div class="family"><div class="eyebrow">Our cultural anchor</div><h2>Oikogéneia · οικογένεια</h2>
    <p>In Greek culture, family is a lasting commitment to care, trust and stewardship across generations. It is the foundation of our approach to the people who use Axía.</p>
    <p>We see subscribers as people making decisions that affect their lives and the people who matter to them—not merely entries in a database. Our responsibility is to present useful evidence clearly, acknowledge uncertainty and help them research with greater confidence, without making their decisions for them.</p></div></section>
    <section class="section"><div class="eyebrow">What guides us</div><h2>Our three core principles</h2>
    <div class="cards">
    <article class="card"><div class="number">01 / VALUE</div><h3>Respect your time.</h3><p><strong>We value our subscribers like family.</strong> Research should clarify rather than overwhelm. Axía brings market developments, company fundamentals and relevant signals into a coherent view.</p><p>Our causal synthesis architecture is designed to connect events to potential business transmission channels, including affected operating metrics and margin drivers. These are analytical interpretations, not certainties.</p></article>
    <article class="card"><div class="number">02 / WORTH</div><h3>Respect the evidence.</h3><p><strong>Trust begins with honest data.</strong> We aim to prioritise traceable company information and distinguish reported figures from estimates and derived calculations.</p><p>Where provider data is incomplete, statement-recovery workflows can use available filings and calculate metrics such as free cash flow (operating cash flow less capital expenditure). Missing or unverified information should be identified, never silently invented.</p></article>
    <article class="card"><div class="number">03 / MERIT</div><h3>Make the reasoning visible.</h3><p><strong>An investment thesis should earn its place through evidence.</strong> Models need assumptions, limitations and calculations that can be examined and challenged.</p><p>Our research architecture works toward clear source attribution, calculation lineage and validation indicators for metrics, forecasts and scenarios. AI-assisted interpretation is kept distinct from deterministic arithmetic and reported facts.</p></article>
    </div></section>
    <section class="closing"><div class="eyebrow">Our commitment</div><h2>All the evidence. A clearer perspective.</h2>
    <p>Axía exists to help you ask better questions, understand what drives a business and monitor whether the reasons behind an investment still hold. Your decisions remain your own.</p>
    <p class="fine">Axía provides research and information, not personal financial advice. Data, models and AI-generated analysis can contain errors, delays or omissions. Verify important information against primary sources and seek appropriately licensed professional advice where needed.</p></section>
    </div>""", unsafe_allow_html=True)
