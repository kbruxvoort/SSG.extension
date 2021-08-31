from pyrevit import revit, DB


def get_value(fam_type, param):
    value = ""
    if param.StorageType == DB.StorageType.Double:
        value = fam_type.AsDouble(param)
        if value == None:
            value = 0
    elif param.StorageType == DB.StorageType.Integer:
        value = fam_type.AsInteger(param)
        if value == None:
            value = 0
    elif param.StorageType == DB.StorageType.String:
        value = fam_type.AsString(param)
        if value == None:
            value = ""
    elif param.StorageType == DB.StorageType.ElementId:
        id_ = fam_type.AsElementId(param)
        e = revit.doc.GetElement(id_)
        if e:
            value = e.Name
    return value


def get_parameter(param_name, params):
    try:
        return [p for p in params if p.Definition.Name == param_name][0]
    except IndexError:
        return None