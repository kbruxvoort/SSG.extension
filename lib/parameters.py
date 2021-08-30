from previt import revit, DB


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