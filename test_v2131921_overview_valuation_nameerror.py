import ast
def test_vinputs_assignment_precedes_first_read():
    s=open("app.py",encoding="utf-8").read()
    block=s[s.index('_val_conf_text=f"{_val_conf}'):s.index('_val_move=',s.index('_val_conf_text=f"{_val_conf}'))]
    assign=block.index('_vinputs=_vaudit.get("inputs"')
    read=block.index('_derived_fcf=isinstance(_vinputs.get')
    assert assign < read
def test_app_parses():
    ast.parse(open("app.py",encoding="utf-8").read())
