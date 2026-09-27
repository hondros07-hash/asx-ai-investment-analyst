from services.navigation_performance import company_navigation_snapshot, STATE_KEY, TIMING_KEY

def test_same_ticker_reuses_snapshot():
    calls = {"history": 0, "info": 0}
    class Bars:
        empty = False
    def history(t):
        calls["history"] += 1
        return Bars()
    def info(t):
        calls["info"] += 1
        return {"longName": t}
    state = {}
    first = company_navigation_snapshot("ZIP.AX", history, info, state)
    second = company_navigation_snapshot("ZIP.AX", history, info, state)
    assert first[0] is second[0]
    assert calls == {"history": 1, "info": 1}
    assert state[TIMING_KEY]["cache"] == "session"
    company_navigation_snapshot("AAPL", history, info, state)
    assert calls == {"history": 2, "info": 2}

def test_empty_history_is_not_cached():
    class Empty:
        empty = True
    state = {}
    company_navigation_snapshot("XYZ", lambda _: Empty(), lambda _: {}, state)
    assert STATE_KEY not in state
