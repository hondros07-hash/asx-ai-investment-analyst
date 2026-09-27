"""Presentation-only financial statement transformations; never mutate provider data."""
import math
import pandas as pd

def _finite(value):
    return isinstance(value,(int,float)) and math.isfinite(value)

def transform(data,group,mode="Reported values"):
    """Return numeric display frame and provenance; newest period first."""
    periods=data.get("periods") or []
    table=(data.get("statements") or {}).get(group) or {}
    rows=[]
    for label,values in table.items():
        row={"Line item":label}
        for index,period in enumerate(periods):
            current=values.get(period)
            result=current if _finite(current) else None
            if mode=="Period growth":
                result=None
                if index+1<len(periods) and data.get("frequency")!="TTM":
                    previous=values.get(periods[index+1])
                    if _finite(current) and _finite(previous) and previous>0:
                        result=(current/previous-1)*100
            elif mode=="Common size":
                denominator_label="Revenue" if group=="Income Statement" else "Total Assets" if group=="Balance Sheet" else "Operating Cash Flow"
                denominator=((data.get("statements") or {}).get(group) or {}).get(denominator_label,{ }).get(period)
                result=(current/denominator*100) if _finite(current) and _finite(denominator) and denominator>0 else None
                if label in ("Diluted EPS","Diluted Shares"): result=None
            row[period]=result
        rows.append(row)
    return pd.DataFrame(rows,columns=["Line item"]+periods)

def display_frame(data,group,mode,formatter):
    raw=transform(data,group,mode)
    # Format into object-typed columns, never into numeric pandas blocks.
    result=raw.astype(object).copy()
    for index,row in raw.iterrows():
        label=row["Line item"]
        for period in data.get("periods") or []:
            value=row[period]
            shown=formatter(value,ratio=False,eps=label=="Diluted EPS") if mode=="Reported values" else (f"{value:+,.2f}%" if mode=="Period growth" and pd.notna(value) else f"{value:,.2f}%" if pd.notna(value) else "—")
            if mode=="Reported values" and (label,period) in (data.get("derived") or {}): shown+=" †"
            result.at[index,period]=shown
    return result

def row_trend(data,group,label):
    """A sparkline-ready sequence of raw reported/provider-transcribed values, oldest first."""
    values=((data.get("statements") or {}).get(group) or {}).get(label) or {}
    return [values[p] for p in reversed(data.get("periods") or []) if _finite(values.get(p))]

def statement_table(data,group,mode,formatter,reverse=False,sparklines=True):
    """Presentation-only table; sparklines are SVG data URIs, not estimated values."""
    import base64
    result=display_frame(data,group,mode,formatter)
    periods=list(data.get("periods") or [])
    if sparklines:
        icons=[]
        for label in result["Line item"]:
            values=row_trend(data,group,label)
            if len(values)<2 or max(values)==min(values):
                icons.append(None)
                continue
            lo=min(0,min(values)); hi=max(0,max(values))
            span=hi-lo
            bars=[]
            width=72/max(len(values),1)
            for i,value in enumerate(values):
                zero=18-(0-lo)/span*16
                y=18-(value-lo)/span*16
                top=min(y,zero);height=max(abs(zero-y),1)
                color="#169a76" if value>=0 else "#cf354b"
                bars.append(f'<rect x="{i*width+1:.2f}" y="{top:.2f}" width="{max(width-2,1):.2f}" height="{height:.2f}" fill="{color}"/>')
            svg='<svg xmlns="http://www.w3.org/2000/svg" width="74" height="20" viewBox="0 0 74 20">'+''.join(bars)+'</svg>'
            icons.append("data:image/svg+xml;base64,"+base64.b64encode(svg.encode()).decode())
        result.insert(1,"10Y Trend",icons)
    ordered=list(reversed(periods)) if reverse else periods
    return result[["Line item"]+(["10Y Trend"] if sparklines else [])+ordered]
