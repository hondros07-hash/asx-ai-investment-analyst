"""Sector KPI definitions and official disclosure discovery; no unverified figures."""
KPI_DEFINITIONS={
"bnpl":[("Total Transaction Volume (TTV)","Issuer-disclosed transaction volume."),("Net Transaction Margin (NTM)","Issuer-defined margin."),("Bad debts / TTV","Issuer-defined credit losses and denominator."),("Cash EBITDA","Issuer-defined non-IFRS measure and reconciliation."),("Active customers","Issuer-reported definition.")],
"bank":[("Net Interest Margin","Issuer-reported margin."),("Non-performing loans","Issuer-defined credit quality."),("Tier 1 capital","Regulatory capital ratio."),("Credit loss provisions","Issuer-reported provisions.")],
"resources":[("Production volume","Reported commodity units."),("Realised commodity price","Reported price and units."),("Unit cash cost","Issuer-defined cash cost."),("Reserves","Reported reserves.")],
"airline":[("Revenue Passenger Kilometres (RPK)","Issuer-defined traffic and period."),("Available Seat Kilometres (ASK)","Issuer-defined capacity and period."),("Passenger load factor","RPK / ASK; match network and period."),("Unit revenue / RASK","Issuer-defined revenue and capacity basis."),("Unit cost / CASK","Issuer-defined cost and capacity basis."),("Underlying EBIT / operating margin","Issuer definition and reconciliation to statutory figures."),("Operating cash flow","Issuer cash-flow statement."),("Net capital expenditure","Issuer definition and reconciliation."),("Net debt / liquidity","Issuer definition, leases and reconciliation.")],
"general":[("Revenue","Income statement."),("Operating income","Income statement."),("Free cash flow","Cash flow statement.")]}
def disclosure_destinations(ticker):
 symbol=str(ticker or "").strip().upper()
 if symbol in ("QAN.MU","QAN.AX"):
  return [{"label":"Qantas primary ASX issuer announcements","url":"https://www.asx.com.au/markets/company/QAN","status":"Issuer discovery only; QAN.MU is a secondary trading listing. Individual figures remain unverified."}]
 if symbol.endswith(".AX") and symbol[:-3].isalnum():
  return [{"label":"ASX company announcements and reports","url":"https://www.asx.com.au/markets/company/"+symbol[:-3],"status":"Discovery only; individual figures unverified"}]
 return []
def kpi_rows(sector):
 return [{"Metric":name,"Value":"Awaiting filing verification","Evidence":"Official issuer filing required","Definition / verification":description} for name,description in KPI_DEFINITIONS.get(sector,KPI_DEFINITIONS["general"])]
