from Autodesk.Revit.Exceptions import InvalidOperationException

from pyrevit import revit, DB


PARAM_MAP = {
    "STD": DB.BuiltInParameterGroup.PG_CONSTRAINTS,
    "MIN": DB.BuiltInParameterGroup.PG_CONSTRAINTS,
    "MAX": DB.BuiltInParameterGroup.PG_CONSTRAINTS,
    "MODIFY": DB.BuiltInParameterGroup.PG_CONSTRUCTION,
    "ADD": DB.BuiltInParameterGroup.PG_CONSTRUCTION,
    "MAT": DB.BuiltInParameterGroup.PG_MATERIALS,
    "SSG": DB.BuiltInParameterGroup.PG_IDENTITY_DATA,
    "URL": DB.BuiltInParameterGroup.PG_IDENTITY_DATA,
    # "QTY": DB.BuiltInParameterGroup.PG_ADSK_MODEL_PROPERTIES,
    "width": DB.BuiltInParameterGroup.PG_GEOMETRY,
    "depth": DB.BuiltInParameterGroup.PG_GEOMETRY,
    "height": DB.BuiltInParameterGroup.PG_GEOMETRY,
    "length": DB.BuiltInParameterGroup.PG_GEOMETRY,
    "thickness": DB.BuiltInParameterGroup.PG_GEOMETRY,
    "price": DB.BuiltInParameterGroup.PG_DATA,
    "cost": DB.BuiltInParameterGroup.PG_DATA,
    "leed": DB.BuiltInParameterGroup.PG_GREEN_BUILDING,
    "green": DB.BuiltInParameterGroup.PG_GREEN_BUILDING,
    "emission": DB.BuiltInParameterGroup.PG_GREEN_BUILDING,
    "emit": DB.BuiltInParameterGroup.PG_GREEN_BUILDING,
    "recycle": DB.BuiltInParameterGroup.PG_GREEN_BUILDING,
    "lead": DB.BuiltInParameterGroup.PG_CONSTRUCTION,
    "salvage": DB.BuiltInParameterGroup.PG_GREEN_BUILDING,
    "weight": DB.BuiltInParameterGroup.PG_STRUCTURAL
}

CATEGORY_MAP = {
        'Width': 1,
        'Depth': 2,
        'Thickness': 3,
        'Height': 4,
    }

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


def param_has_value(fam_type, parameter):
    if parameter.IsDeterminedByFormula:
        return True
    if parameter.Definition.ParameterType == DB.ParameterType.Text:
        return bool(get_value(fam_type, parameter))
    else:
        return fam_type.HasValue(parameter)
    
    
def split_name(param_name):
    name_split = param_name.split("_")
    prefix = None
    if len(name_split) > 1:
        prefix = name_split[0].strip()
        suffix = " ".join(name_split[1:]).strip()
    else:
        suffix = param_name
    return (prefix, suffix)
    

def sort_parameter_into_group(parameter, param_map_dict):
    if parameter.UserModifiable is False:
        return parameter.Definition.ParameterGroup
    if parameter.Definition.Visible is False:
        return DB.BuiltInParameterGroup.INVALID
    name = parameter.Definition.Name
    prefix, suffix = split_name(name)
    if prefix:
        if prefix.upper() == "ENTER" and suffix.lower() not in param_map_dict:
            return DB.BuiltInParameterGroup.PG_CONSTRUCTION
        for k,v in param_map_dict.items():
            if k.upper() == prefix.upper():
                return v
    if suffix:
        for k,v in param_map_dict.items():
            if k.lower() in suffix.lower():
                return v
    return parameter.Definition.ParameterGroup


def reorder_fetch(parameters):
    pass

def modify_parameter_group(parameter, parameter_group):
    try:
        parameter.Definition.ParameterGroup = parameter_group
    except InvalidOperationException as ie:
        print('"{}" is a builtin parameter and its group cannot be set'.format(parameter.Definition.Name))
        