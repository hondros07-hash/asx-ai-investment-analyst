
import pandas as pd

def compare_snapshots(previous, current, keys=None):
    keys=keys or sorted(set(previous)|set(current))
    rows=[]
    for k in keys:
        a=previous.get(k); b=current.get(k)
        if a==b: direction="UNCHANGED"
        else:
            try:
                direction="IMPROVED" if float(b)>float(a) else "WEAKENED"
            except:
                direction="CHANGED"
        rows.append({"metric":k,"previous":a,"current":b,"change":direction})
    return pd.DataFrame(rows)

def material_changes(comparison):
    if comparison is None or comparison.empty:return comparison
    return comparison[comparison["change"]!="UNCHANGED"].copy()
