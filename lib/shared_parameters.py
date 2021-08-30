from pyrevit import revit, DB
from Autodesk.Revit.Exceptions import ArgumentException, InvalidOperationException


STANDARD_PARAMETERS = {
    "STD_Widths": DB.BuiltInParameterGroup.PG_CONSTRAINTS,
    "MIN_Width": DB.BuiltInParameterGroup.PG_CONSTRAINTS,
    "MAX_Width": DB.BuiltInParameterGroup.PG_CONSTRAINTS,
    "STD_Depths": DB.BuiltInParameterGroup.PG_CONSTRAINTS,
    "MIN_Depth": DB.BuiltInParameterGroup.PG_CONSTRAINTS,
    "MAX_Depth": DB.BuiltInParameterGroup.PG_CONSTRAINTS,
    "STD_Heights": DB.BuiltInParameterGroup.PG_CONSTRAINTS,
    "MIN_Height": DB.BuiltInParameterGroup.PG_CONSTRAINTS,
    "MAX_Height": DB.BuiltInParameterGroup.PG_CONSTRAINTS,
    "INFO_Lead Time": DB.BuiltInParameterGroup.PG_CONSTRUCTION,
    "URL_Warranty": DB.BuiltInParameterGroup.PG_CONSTRUCTION,
    "SSG_Short Description": DB.BuiltInParameterGroup.PG_TEXT,
    "SSG_Long Description": DB.BuiltInParameterGroup.PG_TEXT,
    "URL_Finish Options": DB.BuiltInParameterGroup.PG_MATERIALS,
    "ACTUAL_Weight": DB.BuiltInParameterGroup.PG_STRUCTURAL,
    "ACTUAL_Width": DB.BuiltInParameterGroup.PG_GEOMETRY,
    "ACTUAL_Depth": DB.BuiltInParameterGroup.PG_GEOMETRY,
    "ACTUAL_Height": DB.BuiltInParameterGroup.PG_GEOMETRY,
    "URL_Sustainability": DB.BuiltInParameterGroup.PG_GREEN_BUILDING,
    "TOTAL_List Price": DB.BuiltInParameterGroup.PG_DATA,
    "zC": DB.BuiltInParameterGroup.INVALID,
    "zM": DB.BuiltInParameterGroup.INVALID,
    "zO": DB.BuiltInParameterGroup.INVALID,
    "zP": DB.BuiltInParameterGroup.INVALID,
    "SSGFID": DB.BuiltInParameterGroup.PG_IDENTITY_DATA,
    "SSGTID": DB.BuiltInParameterGroup.PG_IDENTITY_DATA,
    "SSG_Author": DB.BuiltInParameterGroup.PG_IDENTITY_DATA,
    "SSG_Product Code": DB.BuiltInParameterGroup.PG_IDENTITY_DATA,
    "SSG_Toll Free Number": DB.BuiltInParameterGroup.PG_IDENTITY_DATA,
    "URL_Contact Southwest Solutions Group": DB.BuiltInParameterGroup.PG_IDENTITY_DATA,
    "URL_Installation Manual": DB.BuiltInParameterGroup.PG_IDENTITY_DATA,
    "URL_Product Page": DB.BuiltInParameterGroup.PG_IDENTITY_DATA,
    "URL_Specification Manual": DB.BuiltInParameterGroup.PG_IDENTITY_DATA,
}


def get_shared_param_by_name(name):
    app = revit.doc.Application
    shared_parameters_file = app.OpenSharedParameterFile()
    shared_groups = shared_parameters_file.Groups
    params = []
    for group in shared_groups:
        for p in group.Definitions:
            if p.Name == name:
                params.append(p)
    if len(params) > 0:
        return params[0]


def get_all_shared_names():
    app = revit.doc.Application
    shared_parameters_file = app.OpenSharedParameterFile()
    shared_groups = shared_parameters_file.Groups
    params = []
    for group in shared_groups:
        for p in group.Definitions:
            params.append(p.Name)
    return params


# Must be in the context of a Revit Transaction
def replace_with_shared(fam_param, shared_param):
    replaced_param = None
    if fam_param.Definition.Name == shared_param.Name:
        revit.doc.FamilyManager.RenameParameter(
            fam_param, fam_param.Definition.Name + "_Temp"
        )
    try:
        replaced_param = revit.doc.FamilyManager.ReplaceParameter(
            fam_param,
            shared_param,
            fam_param.Definition.ParameterGroup,
            fam_param.IsInstance,
        )

    except InvalidOperationException as ie:
        print("InvalidOperationExcpetion: {}".format(ie))
    except ArgumentException as ae:
        print("ArgumentExcpetion: {}".format(ae))

    return replaced_param


def add_standards():
    params = []
    for fam_param in revit.doc.FamilyManager.Parameters:
        fam_name = fam_param.Definition.Name
        if fam_name in STANDARD_PARAMETERS.keys():
            STANDARD_PARAMETERS.pop(fam_name, None)
            replaced_param = replace_with_shared(
                fam_param, get_shared_param_by_name(fam_name)
            )
            params.append(replaced_param)

    for k, v in STANDARD_PARAMETERS.items():
        shared_param = get_shared_param_by_name(k)
        new_param = revit.doc.FamilyManager.AddParameter(shared_param, v, False)
        params.append(new_param)

    return params
