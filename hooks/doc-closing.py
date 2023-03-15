import os.path as op
from pyrevit import forms, script, EXEC_PARAMS

'''
doc = EXEC_PARAMS.event_args.Document
if doc.IsFamilyDocument:
    response = forms.alert("does {} suck?".format(doc.OwnerFamily.Name or doc.Title), yes=True, no=True)
    if response:
        forms.alert("Quick... delete this before someone finds out")
    else:
        output = script.get_output()
        output.resize(500, 550)
        output.self_destruct(5)
        output.print_image(
            op.join(op.dirname(__file__), op.basename(__file__).replace('.py', '.gif')))
        if EXEC_PARAMS.event_args.Cancellable:
            EXEC_PARAMS.event_args.Cancel()
            '''