
import json, re
from datetime import datetime, timezone

DOCUMENT_SCHEMA = {
 "document_type":"results|trading_update|guidance|capital_raising|m_and_a|director|buyback|dividend|presentation|regulatory|annual_report|other",
 "overall_direction":"positive|negative|neutral|mixed",
 "materiality":"low|medium|high",
 "horizon":"days|1m|3m|6m|12m+",
 "summary":"",
 "key_metrics":[],
 "guidance_changes":[],
 "management_claims":[],
 "risks":[],
 "catalysts":[],
 "thesis_strengthens":[],
 "thesis_weakens":[],
 "what_changed":"",
 "source_quotes_short":[]
}

def build_document_prompt(ticker, title, text):
    return f"""You are the document-intelligence layer of an investment research system.
Analyse ONLY the supplied document text. Do not invent missing values.
Ticker: {ticker}
Document: {title}

Return strict JSON with these keys:
document_type, overall_direction, materiality, horizon, summary,
key_metrics, guidance_changes, management_claims, risks, catalysts,
thesis_strengthens, thesis_weakens, what_changed, source_quotes_short.

For each key metric use:
{{"metric":"","current":"","prior":"","change":"","unit":"","page_or_location":"","interpretation":""}}

For management claims use:
{{"claim":"","evidence_in_document":"","status":"supported|unsupported|not_yet_testable"}}

Keep source_quotes_short very short. Document text:
{text[:120000]}
"""

def analyse_with_openai(client, ticker, title, text, model="gpt-5.6"):
    prompt=build_document_prompt(ticker,title,text)
    response=client.responses.create(
        model=model,
        input=prompt
    )
    raw=response.output_text.strip()
    raw=re.sub(r"^```json\s*|\s*```$","",raw,flags=re.I|re.S)
    return json.loads(raw)
