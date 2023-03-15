import re
from System.Collections.Generic import List

from pyrevit import revit, DB, forms
from parameters.family import (
    param_has_value, 
    split_name, 
    sort_parameter_into_group, 
    PARAM_MAP, 
    CATEGORY_MAP, 
    modify_parameter_group
)


def prefix_sort(param):
    name = param.Definition.Name
    return split_name(name)


def suffix_sort(param):
    name = param.Definition.Name
    return split_name(name)[1]


def constraints_sort(param):
    name = param.Definition.Name
    prefix, suffix = split_name(name)
    if "width" in suffix.lower():
        group = 0
    elif "depth" in name.lower():
        group = 1
    elif "height" in name.lower():
        group = 2
    else:
        group = 3
    if prefix == 'STD':
        prefix_order = 0
    elif prefix == 'MIN':
        prefix_order = 1
    elif prefix == 'MAX':
        prefix_order = 2
    else:
        prefix_order = 3
        
    return (group, prefix_order, name)


def identity_sort(param):
    name = param.Definition.Name
    # prefix, suffix = split_name(name)
    if name == "SSGFID":
        group = 0
    elif name == "SSGTID":
        group = 1
    elif name == "SSG_Author":
        group = 2
    elif name == "SSG_Product Code":
        group = 3
    elif name == "SSG_Toll Free Number":
        group = 4
    elif name == "Manufacturer":
        group = 5
    elif name == "Assembly Code":
        group = 6
    elif name == "Keynote":
        group = 7
    else:
        group = 8
    
    current_type = revit.doc.FamilyManager.CurrentType  
    has_value = param_has_value(current_type, param)
        
    return (group, not(has_value), name)
  
    
def lengths_sort(param):
    name = param.Definition.Name
    actual_pattern = re.compile(r'^ACTUAL_(.*)$')
    category_match = re.search(r'(Width|Depth|Thickness|Height)', name)
    if category_match:
        category = category_match.group(0)
        category_order = CATEGORY_MAP.get(category, 0)
    else:
        category_order = 0
        
    actual_match = actual_pattern.search(name)
    is_actual = bool(actual_match)
    
    return (category_order, is_actual, name)


def default_sort(param):
    current_type = revit.doc.FamilyManager.CurrentType
    has_value = param_has_value(current_type, param)
    name = param.Definition.Name
    instance = param.IsInstance
    param_type = param.Definition.ParameterType
    return (not(has_value), not(instance), param_type, name)


SORT_FUNCTIONS = {
    DB.BuiltInParameterGroup.PG_IDENTITY_DATA: identity_sort,
    DB.BuiltInParameterGroup.PG_GEOMETRY: lengths_sort,
    DB.BuiltInParameterGroup.PG_CONSTRAINTS: constraints_sort,
}


params = revit.doc.FamilyManager.Parameters
param_dict = {
    "None": []
}

for p in params:
    group = sort_parameter_into_group(p, PARAM_MAP)
    if group:
        if group in param_dict:
            param_dict[group].append(p)
        else:
            param_dict[group] = [p]
    else:
        param_dict["None"].append(p)
        
for key, value in param_dict.items():
    sort_func = SORT_FUNCTIONS.get(key, default_sort)
    param_dict[key] = sorted(value, key=sort_func)


with revit.Transaction("Reorder parameters"):
    param_list = List[DB.FamilyParameter]()
    current_type = revit.doc.FamilyManager.CurrentType
    for k,v in param_dict.items():
        for param in v:
            if param.UserModifiable:
                modify_parameter_group(param, k)
            param_list.Add(param)

    revit.doc.FamilyManager.ReorderParameters(param_list)
    
forms.alert("Reorder complete", warn_icon=False)
