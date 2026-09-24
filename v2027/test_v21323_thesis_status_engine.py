from services.thesis_status_engine import calculate_thesis_status
def test_pending_is_not_failure():
 r=calculate_thesis_status({"a":True,"b":None,"c":None},expected_total=6)
 assert r["on_track_count"]==1 and r["watch_count"]==0 and r["pending_count"]==5 and r["status_label"]=="Insufficient Evidence"
def test_watch_requires_evidence():
 r=calculate_thesis_status({"a":True,"b":False,"c":True},expected_total=6)
 assert r["status_label"]=="Watch" and r["watch_count"]==1
def test_on_track_when_sufficient_and_no_watch():
 r=calculate_thesis_status({"a":True,"b":True,"c":True,"d":None},expected_total=6)
 assert r["status_label"]=="On Track"
def test_all_conditions_on_track():
 r=calculate_thesis_status({str(i):True for i in range(6)},expected_total=6)
 assert r["status_label"]=="All Conditions On Track"
def test_ai_never_calculates():
 assert calculate_thesis_status({},6)["provenance"]["ai_calculated"] is False
def test_boolean_false_is_watch_not_missing():
 r=calculate_thesis_status({"x":False},expected_total=1)
 assert r["watch_count"]==1 and r["pending_count"]==0
