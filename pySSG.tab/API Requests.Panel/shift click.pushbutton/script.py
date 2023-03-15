import config

from pyrevit import revit, DB
from parameters import shared

standard_params = config.load_configs()

if standard_params:
    for sp in standard_params:
        print(sp.Name)
    # print(source_selection)
#     view_type = [x for x in revit.query.get_types_by_class(DB.ViewFamilyType) if source_selection.lower() in revit.query.get_name(x).lower()]
#     # for item in source_selection:
#     #     print(item)
#     print(revit.query.get_name(view_type[0]), view_type[0].Id)

# default_elevation = revit.doc.GetDefaultElementTypeId(DB.ElementTypeGroup.ViewTypeElevation)
# print("Default Id: ", default_elevation)
# types = revit.query.get_types_by_class(DB.ViewFamilyType)
# for v_type in types:
#     print(revit.query.get_name(v_type), v_type.ViewFamily)

# revit.query.id