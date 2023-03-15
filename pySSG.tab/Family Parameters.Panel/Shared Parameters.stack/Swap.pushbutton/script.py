from pyrevit import revit, DB, forms
from parameters import SharedParameterFile, replace_with_shared


def filt_func(parameter):
    shared_names = [d.Name.lower() for d in SharedParameterFile().list_definitions()]
    return not parameter.IsShared and parameter.Definition.Name.lower() in shared_names
    
def_file = SharedParameterFile()
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
                shared_param = def_file.query(name=sp.Definition.Name, first_only=True)
                if shared_param:
                    replaced = replace_with_shared(sp, shared_param)
                    if replaced:
                        count += 1
        forms.alert("{} parameters successfully swapped".format(count))

