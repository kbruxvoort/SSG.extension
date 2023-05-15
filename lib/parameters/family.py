from Autodesk.Revit.Exceptions import InvalidOperationException, ArgumentException

from pyrevit import revit, DB, HOST_APP



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
        

def is_built_in(family_parameter):
    return family_parameter.Definition.BuiltInParameter != DB.BuiltInParameter.INVALID
    

def get_parameter_type_name(family_parameter):
    if HOST_APP.is_newer_than(2022, or_equal=True):
        return DB.LabelUtils.GetLabelForSpec(family_parameter.Definition.GetDataType())
    else:
        return family_parameter.Definition.ParameterType.ToString()
    

def get_name(family_parameter):
    return family_parameter.Definition.Name

          
def get_value(family_parameter, family_type):
    if family_parameter.StorageType == DB.StorageType.Double:
        return family_type.AsDouble(family_parameter)

    elif family_parameter.StorageType == DB.StorageType.Integer:
        return family_type.AsInteger(family_parameter)

    elif family_parameter.StorageType == DB.StorageType.String:
        return family_type.AsString(family_parameter)

    elif family_parameter.StorageType == DB.StorageType.ElementId:
        id_ = family_type.AsElementId(family_parameter)
        return revit.doc.GetElement(id_)
        

def split_name(family_parameter):
    name_split = family_parameter.Definition.Name.split("_")
    prefix = None
    if len(name_split) > 1:
        prefix = name_split[0].strip()
        suffix = " ".join(name_split[1:]).strip()
    else:
        suffix = family_parameter.Definition.Name
    return (prefix, suffix)
    

def has_value(family_parameter, family_type):
    if family_parameter.IsDeterminedByFormula:
        return True
    if HOST_APP.is_newer_than(2022, or_equal=True):
        is_text = family_parameter.Definition.GetDataType() == DB.SpecTypeId.String
    else:
        is_text = family_parameter.Definition.ParameterType == DB.ParameterType.Text
    if is_text:
        return bool(get_value(family_parameter, family_type))
    else:
        return family_type.HasValue(family_parameter)
        

def modify_group(family_parameter, new_group):
    if not is_built_in(family_parameter):
        family_parameter.Definition.ParameterGroup = new_group
            

def get_sorted_group(family_parameter, param_map_dict):
    if not is_built_in(family_parameter):
        if family_parameter.Definition.Visible is False:
            return DB.BuiltInParameterGroup.INVALID
        prefix, suffix = split_name(family_parameter)
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
    return family_parameter.Definition.ParameterGroup
    

def param_associated_to_array(family_parameter, array_element_ids):
    if family_parameter.AssociatedParameters:
        for ap in family_parameter.AssociatedParameters:
            if ap.Element.GroupId in array_element_ids:
                return True
    return False
    

def get_array_original_element_ids(family_document):
    arrays = DB.FilteredElementCollector(family_document).OfCategory(DB.BuiltInCategory.OST_IOSArrays).ToElements()
    array_element_ids = []
    for a in arrays:
        array_element_ids.extend(a.GetOriginalMemberIds())
    return array_element_ids        


def save_param_order(family_document):
    fam_mgr = family_document.FamilyManager
    sort_index = 0
    param_dict = {}
    for p in fam_mgr.GetParameters():
        param_dict[p.Definition.Name] = sort_index
        sort_index += 1
    return param_dict


def sort_parameter_into_group(parameter, param_map_dict):
    if parameter.UserModifiable is False:
        return parameter.Definition.ParameterGroup
    if parameter.Definition.Visible is False:
        return DB.BuiltInParameterGroup.INVALID
    prefix, suffix = split_name(parameter)
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

        
def replace_with_shared(family_parameter, external_definition):
    if family_parameter.Definition.Name == external_definition.Name:
        revit.doc.FamilyManager.RenameParameter(
            family_parameter, family_parameter.Definition.Name + "_Temp"
        )
    try:
        return revit.doc.FamilyManager.ReplaceParameter(
            family_parameter,
            external_definition,
            family_parameter.Definition.ParameterGroup,
            family_parameter.IsInstance,
        )

    except InvalidOperationException as ie:
        print("InvalidOperationExcpetion: {}".format(ie))
    except ArgumentException as ae:
        print("ArgumentExcpetion: {}".format(ae))

    