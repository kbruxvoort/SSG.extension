import clr

clr.AddReference("RevitAPI")
from Autodesk.Revit.DB import *
from pyrevit import revit, DB, UI
from pyrevit import script
from pyrevit import forms
import System
from System.Collections.Generic import *


def share_match(share_file, name):
    for group in share_file.Groups:
        for shared_param in group.Definitions:
            if name == shared_param.Name:
                return shared_param
            else:
                pass


std_params = {
    "STD_Widths": BuiltInParameterGroup.PG_CONSTRAINTS,
    "MIN_Width": BuiltInParameterGroup.PG_CONSTRAINTS,
    "MAX_Width": BuiltInParameterGroup.PG_CONSTRAINTS,
    "STD_Depths": BuiltInParameterGroup.PG_CONSTRAINTS,
    "MIN_Depth": BuiltInParameterGroup.PG_CONSTRAINTS,
    "MAX_Depth": BuiltInParameterGroup.PG_CONSTRAINTS,
    "STD_Heights": BuiltInParameterGroup.PG_CONSTRAINTS,
    "MIN_Height": BuiltInParameterGroup.PG_CONSTRAINTS,
    "MAX_Height": BuiltInParameterGroup.PG_CONSTRAINTS,
    "INFO_Lead Time": BuiltInParameterGroup.PG_CONSTRUCTION,
    "URL_Warranty": BuiltInParameterGroup.PG_CONSTRUCTION,
    "SSG_Short Description": BuiltInParameterGroup.PG_TEXT,
    "SSG_Long Description": BuiltInParameterGroup.PG_TEXT,
    "URL_Finish Options": BuiltInParameterGroup.PG_MATERIALS,
    "ACTUAL_Weight": BuiltInParameterGroup.PG_STRUCTURAL,
    "ACTUAL_Width": BuiltInParameterGroup.PG_GEOMETRY,
    "ACTUAL_Depth": BuiltInParameterGroup.PG_GEOMETRY,
    "ACTUAL_Height": BuiltInParameterGroup.PG_GEOMETRY,
    "URL_Sustainability": BuiltInParameterGroup.PG_GREEN_BUILDING,
    "TOTAL_List Price": BuiltInParameterGroup.PG_DATA,
    "zC": BuiltInParameterGroup.INVALID,
    "zM": BuiltInParameterGroup.INVALID,
    "zO": BuiltInParameterGroup.INVALID,
    "zP": BuiltInParameterGroup.INVALID,
    "SSGFID": BuiltInParameterGroup.PG_IDENTITY_DATA,
    "SSGTID": BuiltInParameterGroup.PG_IDENTITY_DATA,
    "SSG_Author": BuiltInParameterGroup.PG_IDENTITY_DATA,
    "SSG_Product Code": BuiltInParameterGroup.PG_IDENTITY_DATA,
    "SSG_Toll Free Number": BuiltInParameterGroup.PG_IDENTITY_DATA,
    "URL_Contact Southwest Solutions Group": BuiltInParameterGroup.PG_IDENTITY_DATA,
    "URL_Installation Manual": BuiltInParameterGroup.PG_IDENTITY_DATA,
    "URL_Product Page": BuiltInParameterGroup.PG_IDENTITY_DATA,
    "URL_Specification Manual": BuiltInParameterGroup.PG_IDENTITY_DATA,
}

logger = script.get_logger()

# ensure active document is a family document
forms.check_familydoc(revit.doc, exitscript=True)

app = revit.doc.Application
# make sure user has saved open models in case the tool crashes
if not forms.alert(
    "Make sure your models are saved and synced. " "Hit OK to continue...", cancel=True
):
    script.exit()

# get current shared parameter file
sharedParametersFile = app.OpenSharedParameterFile()
sharedGroups = sharedParametersFile.Groups

# get current family parameters
family_params = revit.doc.FamilyManager.GetParameters()

existing_list = []
replace_list = []
shared_replace_list = []

for fparam in family_params:
    for key, values in std_params.items():
        if fparam.Definition.Name == key:
            del std_params[key]
            if fparam.IsShared:
                message = '"%s" is already in this family' % fparam.Definition.Name
                logger.warning(message)
                continue
            else:
                replace_list.append(fparam)

for replace_param in replace_list:
    shared_replace_list.append(
        share_match(sharedParametersFile, replace_param.Definition.Name)
    )
    # print replace_param
    # print(share_match(sharedParametersFile, replace_param.Definition.Name).Name)

# define a transaction variable and describe the transaction
with revit.Transaction("Add standard parameters"):
    for r, s in zip(replace_list, shared_replace_list):
        try:
            print(
                'Replacing "{}" with Shared Parameter ({})'.format(
                    r.Definition.Name, s.Name
                )
            )
            # Revit doesn't like it if the old parameter has the same name as the new one so we much change it first
            revit.doc.FamilyManager.RenameParameter(r, r.Definition.Name + "_Old")
            new_param = revit.doc.FamilyManager.ReplaceParameter(
                r, s, r.Definition.ParameterGroup, r.IsInstance
            )
        except:
            logger.error('Failed to Replace "{}"'.format(r.Definition.Name))

    for key, value in std_params.items():
        shared_param = share_match(sharedParametersFile, key)
        try:
            print(
                'Adding "{}" Shared Parameter to Group ({})'.format(
                    shared_param.Name, value
                )
            )
            new_param = revit.doc.FamilyManager.AddParameter(shared_param, value, False)
        except:
            logger.error("Failed to Add Parameter")

print("Done")
