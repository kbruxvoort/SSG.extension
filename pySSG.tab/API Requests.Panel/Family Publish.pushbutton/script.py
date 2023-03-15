import os
import json


from System import Guid
from pyrevit import forms, revit, DB

from fetch_client import Client, Family, FamilyType, Parameter, File, get_family_id, file_from_path, get_auth
from parameters import SharedParameterFile
from parameters.family import get_value, param_has_value
from pyssg_utils import to_list



class FamTypeItem(forms.TemplateListItem):
    pass


def get_id_params(family_document, ext_dict):
    # Needs to be wrapped in a transaction
    sp_file = SharedParameterFile()
    family_manager = family_document.FamilyManager
    for k,v in ext_dict.items():
        param = family_manager.get_Parameter(Guid(v.get("GUID")))
        if not param:
            ext_def = sp_file.query(guid=v.get("GUID"))
            if ext_def:
                param = fam_mgr.AddParameter(ext_def, v.get("Group"), False)
        ext_dict[k]["Parameter"] = param
    return ext_dict


def match_types(family_types, db_types):
    type_map = {}
    count = 1
    for dt in db_types:
        for ft in family_types:
            if dt.Name == ft.Name:
                type_map[dt.Name] = {"fam_type": ft, "db_type": dt, "db_id": dt.Id, "zO": count}
                break
    return type_map


def set_type_id_formula(family_document, type_map_dict, ssgtid_param, zo_param):
    family_manager = family_document.FamilyManager
    formula = ""
    
    if len(type_map_dict) == 1:
        first_key = list(type_map_dict.keys())[0]
        value = type_map_dict[first_key]
        family_manager.CurrentType = value["fam_type"]
        family_manager.Set(zo_param, value["zO"])
        formula = '"{}"'.format(value["db_type"].Id)
    
    else:
        for _, value in type_map_dict.items():
            family_manager.CurrentType = value["fam_type"]
            family_manager.Set(zo_param, value["zO"])
            formula += 'if(zO = {}, "{}", '.format(value["zO"], value["db_type"])
        formula = formula + '"ERROR"' + (")" * (len(type_map_dict)))
    
    if formula:
        return family_manager.SetFormula(ssgtid_param, formula)


def create_shell_object(family_document):
    family_manager = family_document.FamilyManager
    family_types = [ft for ft in fam_mgr.Types if len(ft.Name) > 1]
    default_type = family_manager.CurrentType
    family_name = family_document.Title
    family_category = family_document.OwnerFamily.FamilyCategory.Name
    if len(family_types) > 1:
        default_type = forms.SelectFromList.show(
            sorted([FamTypeItem(ft, name_attr='Name') for ft in fam_types], key=lambda t: t.Name),
            title="Select Default Type",
            button_name="Select",
            multiselect=False
        )
        
    shell_fam = Family(Name=family_name, CategoryName=family_category, FamilyObjectType="Family", Status=2, LoadMethod=0)
    shell_fam.FamilyTypes = [FamilyType(Name=t.Name, IsDefault=t.Name==default_type.Name) for t in fam_types]
    
    fam_dict = fetch.families.create(shell_fam.to_dict())
    if fam_dict:
        return Family.from_dict(fam_dict)
    

def modify_global_db_parameters(family_document, parameters, db_object):
    family_manager = family_document.FamilyManager
    current_type = family_manager.CurrentType
    parameters = to_list(parameters)
    for p in parameters:
        value = get_value(current_type, p)
        if p.IsInstance:
            pt_value = "Instance"
        else:
            pt_value = "Type"
        match = False
        for dp in db_object.Parameters:
            if dp.Name == p.Definition.Name:
                # dp.Deleted=True
                dp.Value=str(value),
                dp.ParameterType=pt_value
                match = True
                break
        if match is False:
            db_param = Parameter(
                Name=p.Definition.Name, 
                Value=str(value),
                ParameterId=None,
                ParameterType=pt_value,
                DataType=str(p.Definition.ParameterType)
                )
            db_object.Parameters.append(db_param)
    return db_object


def modify_type_db_parameters(family_document, parameters, db_object, type_map_dict):
    family_manager = family_document.FamilyManager
    current_type = family_manager.CurrentType
    parameters = to_list(parameters)
    for _, v in type_map_dict.items():
        current_type = v["fam_type"]
        db_type = [dt for dt in db_object.FamilyTypes if dt.Id == v["db_id"]][-1]
        for p in parameters:
            match = False
            value = get_value(current_type, p)
            for dp in db_type.Parameters:
                if dp.Name == p.Definition.Name:
                    # dp.Deleted = True
                    dp.Value = str(value)
                    match = True
                    break
            if match is False:
                db_param = Parameter(
                    Name=p.Definition.Name, 
                    Value=str(value),
                    ParameterId=0,
                    ParameterType="Type",
                    DataType=str(p.Definition.ParameterType)
                )
                db_type.Parameters.append(db_param)
    return db_object


IDENTITY_DEFS = {
    "SSGFID": {"GUID": "cd2bd688-6eb7-4586-ba8c-148a0d1c845c", "Group": DB.BuiltInParameterGroup.PG_IDENTITY_DATA},
    "SSGTID": {"GUID": "72652635-8cde-4ba9-9752-64a47828a94c", "Group": DB.BuiltInParameterGroup.PG_IDENTITY_DATA},
    "ZO": {"GUID": "2787c588-ec10-47c4-b44f-736dcd28e8d9", "Group": DB.BuiltInParameterGroup.INVALID}
}

save_ops = DB.SaveAsOptions()
save_ops.OverwriteExistingFile = True
save_ops.Compact = True
fam_mgr = revit.doc.FamilyManager
owner_fam = revit.doc.OwnerFamily
name = revit.doc.Title
category = owner_fam.FamilyCategory.Name
fam_types = [ft for ft in fam_mgr.Types if len(ft.Name) > 1]

# Make sure they have access to API
BIM_KEY = get_auth()
if not BIM_KEY:
    forms.alert("No API token found", exitscript=True)

fetch = Client(auth=BIM_KEY)

# Check if family has a Family Id
fam = None
create_shell = False
file_only = False
ssgfid = get_family_id(revit.doc)
if not ssgfid:
    create_shell = True
else:
    fam_dict = fetch.families.retrieve(ssgfid)
    if not fam_dict:
        create_shell = True
    else:
        # print(fam_dict)
        fam = Family.from_dict(fam_dict)
        override_options = forms.alert(
            msg="This family contains an SSGFID currently associated with database object '{}'. " \
                "Any updates will overwrite parts of this object. How would you like to continue?".format(fam.Name),
            title="Overwrite existing object?",
            options=["Overwrite existing", "Create new object", "Update file only"],
        )
        if override_options == "Overwrite existing":
            pass
        elif override_options == "Create new object":
            create_shell = True
        elif override_options == "Update file only":
            file_only = True

# If family doesn't have a database object create a shell object
if create_shell:
    create_option = forms.alert(
        msg="No Family Id found. Would you like to create a database object?",
        yes=True,
        no=True,
        ok=False,
        exitscript=True
    )
    
    # create shell family
    if create_option:
        fam = create_shell_object(revit.doc)


        
if fam:
    response=None
    with revit.Transaction("Set ID Parameters"):
        param_dict = get_id_params(revit.doc, IDENTITY_DEFS)
        
        # Set SSGFID to match Database
        fam_mgr.SetFormula(param_dict['SSGFID']["Parameter"], '"{}"'.format(fam.Id))
        
        # Map family types to database types
        type_map = match_types(fam_types, fam.FamilyTypes)
        
        # Set SSGTID to match Database
        ssgtid_param = set_type_id_formula(revit.doc, type_map, param_dict["SSGTID"]["Parameter"], param_dict["ZO"]["Parameter"])
        

            
    # Select parameters to sync to database
    if file_only is False:
        fam.Parameters = [p for p in fam.Parameters if p.ParameterId != -1]
        global_names = []
        selected_global_params = forms.select_family_parameters(
            revit.doc,
            title='Select global family parameters',
            filterfunc=lambda x: not(x.IsDeterminedByFormula) and param_has_value(fam_mgr.CurrentType, x)
        )

        if selected_global_params:
            global_names = [g.Definition.Name for g in selected_global_params]
            
        selected_type_params = forms.select_family_parameters(
            revit.doc,
            title="Select parameters to save per family type",
            include_instance=False,
            filterfunc=lambda x: x.Definition.Name not in global_names and not(x.IsDeterminedByFormula) and param_has_value(fam_mgr.CurrentType, x)
        )

        # Add global parameters to database object
        if selected_global_params:
            fam = modify_global_db_parameters(revit.doc, selected_global_params, fam)

        # Add type parameters to database object types
        # if selected_type_params:
        #     fam = modify_type_db_parameters(revit.doc, selected_type_params, fam, type_map)


        fam.Name = name
        fam.CategoryName = category
        
        file_path = revit.doc.PathName
        if not file_path:
            file_path = forms.save_file(file_ext="rfa")
        revit.doc.SaveAs(file_path, save_ops)
        revit_file = File.file_from_path(file_path, file_key="FamilyRevitFile")
        fam.Files.append(revit_file)
        # print(json.dumps(fam.to_dict(), indent=4))
        response = fetch.families.create(fam.to_dict())
        
    else:
        # publish file only
        file_path = revit.doc.PathName
        if not file_path:
            file_path = forms.save_file(file_ext="rfa")
        revit.doc.SaveAs(file_path, save_ops)
        revit_file = File.file_from_path(file_path, file_key="FamilyRevitFile")

        data={
            "FamilyId": fam.Id,
            "Files": [revit_file.to_dict()]
        }
        # print(data)
        response = fetch.families.update(data=data)
    if response:
        forms.alert(
            msg="Successfully saved '{}'".format(fam.Name),
            warn_icon=False
        )
    # print(response)

# ssgfid = get_family_id(revit.doc)
# fam_dict = fetch.families.retrieve(ssgfid)
# print(fam_dict.keys())
# print(fam_dict.get('FamilyTypes'))       
# else:
#     fam_dict = fetch.families.retrieve(ssgfid)
    
# ssgfid_value = '""'.format(fam_dict.get('Id'))
# ssgtid_value = fam_dict.get('Id')
        
    
# set SSGFID and SSGTID

# get type parameters to be saved

# get family parameters to be saved

# save file

# update database object
# file_data = file_from_path(revit.doc.PathName)
# file_name, extension = revit.doc.PathName.split("\\")[-1].split(".")
# data={
#     "FamilyId": ssgfid,
#     "Files": [
#         {
#             "FileId": None,
#             "FileName": file_name,
#             "FileExtension": "." + extension,
#             "FileKey": "FamilyRevitFile",
#             "FileData": file_data
#         }
#     ]
# }
# r2 = fetch.families.update(data=data)
# if r2:
#     forms.alert(
#         msg="Successfully saved '{}'".format(file_name + "." + extension),
#         warn_icon=False
#                     )
