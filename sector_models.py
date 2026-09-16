
SECTOR_KPIS={
 "Banks":["net_interest_margin","cet1","bad_debts","roe","loan_growth","deposit_growth"],
 "Mining":["production","realised_commodity_price","aisc_or_unit_cost","reserves","capex","free_cash_flow"],
 "Technology":["arr","recurring_revenue","customer_growth","churn","gross_margin","free_cash_flow"],
 "Retail":["same_store_sales","gross_margin","inventory_growth","store_growth","operating_margin"],
 "REIT":["ffo","occupancy","wale","gearing","nav_or_nta","distribution"],
 "Healthcare":["revenue_growth","pipeline","approvals","r_and_d","cash_burn","gross_margin"],
 "BNPL/Fintech":["ttv","active_customers","transaction_margin","credit_losses","revenue_growth",
                 "cash_ebitda","operating_margin","us_growth","international_growth","regulatory_risk"]
}

def kpis_for(sector):
    return SECTOR_KPIS.get(sector,[])
