from pyrevit import revit, DB


def get_placed_rooms(project_document):
    area_param_id = DB.ElementId(DB.BuiltInParameter.ROOM_AREA)
    area_param_prov = DB.ParameterValueProvider(area_param_id)
    param_greater = DB.FilterNumericGreater()
    filt = DB.ElementParameterFilter(
        DB.FilterDoubleRule(area_param_prov, param_greater, 0, 1e-6)
    )

    return DB.FilteredElementCollector(project_document).WherePasses(filt).ToElements()
