from pyrevit import revit, DB, forms
from parameters import shared


app = revit.doc.Application

def filt_func(parameter):
    def_groups = shared.get_groups(app)
    shared_names = []
    for group in def_groups:
        for definition in group.Definitions:
            shared_names.append(definition.Name)
            
    return not parameter.IsShared and parameter.Definition.Name in shared_names
    
def_file = app.OpenSharedParameterFile()
if not def_file:
    def_file = shared.set_file(app)
    
if not def_file:
    forms.alert("Shared parameter file could not be found")
else:
    match = False
    params = revit.doc.FamilyManager.Parameters
    for p in params:
        if filt_func(p):
            match = True
            break
    
    if not match:
        forms.alert("No potential swaps")
    else:
        selected_params = forms.select_family_parameters(revit.doc, title='Parameters to swap', include_builtin=False, filterfunc=filt_func )

        if selected_params:
            with revit.Transaction("Swap family parameters for shared"):
                count = 0
                for sp in selected_params:
                    shared_param = shared.query(app, name=sp.Definition.Name)
                    if shared_param:
                        replaced = shared.replace_with_shared(sp, shared_param)
                        if replaced:
                            count += 1
            forms.alert("{} parameters successfully swapped".format(count))

