from pyrevit import revit, DB
from shared_parameters import (
    get_all_shared_names,
    replace_with_shared,
    get_shared_param_by_name,
)


family_params = revit.doc.FamilyManager.Parameters

shared_names = get_all_shared_names()
with revit.Transaction("Replace parameters with shared"):
    for param in family_params:
        if not param.IsShared and param.Definition.Name in shared_names:
            replaced_param = replace_with_shared(
                param, get_shared_param_by_name(param.Definition.Name)
            )
