import json

from System.Net import WebClient

from pyrevit import revit, forms, DB
from fetchbim.family import Family, FamilyType
from fetchbim import settings
from fetchbim.attributes import Parameter, File


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


if settings.BIM_KEY:

    client = WebClient()
    client.Headers.Add("Authorization", settings.BIM_HEADERS["Authorization"])
    client.Headers.Add("Accept", "application/json")
    client.Headers.Add("Content-Type", "application/json")
    url = settings.POST_FAMILY
    name = revit.doc.Title
    file_path = revit.doc.PathName
    fam_mgr = revit.doc.FamilyManager
    family_types = fam_mgr.Types
    default_type = fam_mgr.CurrentType
    default_name = default_type.Name
    owner_fam = revit.doc.OwnerFamily
    category = owner_fam.FamilyCategory.Name
    start_fam = Family(name, CategoryName=category)
    params = fam_mgr.Parameters
    instance = [p for p in params if p.IsInstance]
    ssgfid = [p for p in params if p.Definition.Name == "SSGFID"]
    type_params_names, global_params_names = [], []

    print("Checking SSGFID")
    if ssgfid:
        id_ = get_value(default_type, ssgfid[0])
        if id_:
            exists = True
            print(
                "\tIdentity parameters exist. Getting parameter list from database..."
            )
            get_url = settings.GET_FAMILY.format(id_)
            business_fams = json.loads(client.DownloadString(get_url)).get(
                "BusinessFamilies"
            )
            if business_fams:
                fam = Family.from_json(business_fams[0])
                print("\tMatch Found: {}".format(fam))
                # print('Parameters to update')
                # type_param_names = [p.Name for p in ft.Parameters for ft in fam.FamilyTypes]
                global_params = [x for x in fam.Parameters]

                type_match = []
                for db_type in fam.FamilyTypes:
                    for revit_type in family_types:
                        if db_type.Name == revit_type.Name:
                            type_match.append((db_type, revit_type))

                for db_type, revit_type in type_match:
                    for p in params:
                        for p2 in db_type.Parameters:
                            if p.Definition.Name == p2.Name:
                                p2.Value = get_value(revit_type, p)

                if global_params:
                    for p in params:
                        for gp in global_params:
                            if p.Definition.Name == gp.Name:
                                gp.Value = get_value(fam_mgr.CurrentType, p)

        else:
            exists = False
            type_params = forms.select_family_parameters(
                revit.doc, title="Select Family Type Parameters", include_instance=False
            )
            if type_params:
                type_params_names = [x.Definition.Name for x in type_params]
                global_params = forms.select_family_parameters(
                    revit.doc,
                    title="Select Global Parameters",
                    filterfunc=lambda x: x.Definition.Name not in type_params_names,
                )
                if global_params:
                    global_params_names = [x.Definition.Name for x in global_params]

    else:
        print("\tSSGFID parameter doesn't exist")
        app = revit.doc.Application
        sharedParametersFile = app.OpenSharedParameterFile()
        sharedGroups = sharedParametersFile.Groups
        id_group = [
            group.Definitions for group in sharedGroups if group.Name == "Identity Data"
        ]

        if id_group:
            group_definitions = id_group[0]
            ssgfid_param = [x for x in group_definitions if x.Name == "SSGFID"]
            ssgtid_param = [x for x in group_definitions if x.Name == "SSGTID"]

            for fam_type in family_types:
                if len(fam_type.Name) > 1:
                    if fam_type.Name == default_name:
                        ft = FamilyType(fam_type.Name, IsDefault=True)
                    else:
                        ft = FamilyType(fam_type.Name)
                    start_fam.FamilyTypes.append(ft)

            shell_data = start_fam.to_json()
            response = client.UploadString(url, "POST", shell_data)
            # print(response)
            fam_json = json.loads(response)
            fam = Family.from_json(fam_json)
            print("\t[{}] Shell Family Created".format(fam.Id))

            with revit.Transaction("Add Identity Parameters"):
                print("\tAdding SSGFID")
                fam_id_param = fam_mgr.AddParameter(
                    ssgfid_param[0], DB.BuiltInParameterGroup.PG_IDENTITY_DATA, False
                )
                print("\tAdding SSGTID")
                type_id_param = fam_mgr.AddParameter(
                    ssgtid_param[0], DB.BuiltInParameterGroup.PG_IDENTITY_DATA, False
                )
                zO_param = [p for p in params if p.Definition.Name == "zO"]
                if not zO_param:
                    other_group = [
                        group.Definitions
                        for group in sharedGroups
                        if group.Name == "Other"
                    ]
                    if other_group:
                        other_definitions = other_group[0]
                        zO_param = [x for x in other_definitions if x.Name == "zO"]
                        print("\tAdding zO")
                        zO_param = fam_mgr.AddParameter(
                            zO_param[0], DB.BuiltInParameterGroup.INVALID, False
                        )
                else:
                    zO_param = zO_param[0]
                fam_mgr.SetFormula(fam_id_param, '"{}"'.format(fam.Id))
                if len(fam.FamilyTypes) > 1:
                    type_matches = []
                    formula = ""
                    count = 0
                    for revit_type in family_types:
                        for db_type in fam.FamilyTypes:
                            db_type.FamilyId = fam.Id
                            if revit_type.Name == db_type.Name:
                                count += 1
                                fam_mgr.CurrentType = revit_type
                                fam_mgr.Set(zO_param, count)
                                formula += 'if(zO = {}, "{}", '.format(
                                    count, db_type.Id
                                )
                                type_matches.append((revit_type, db_type, count))
                    formula = formula + '"ERROR"' + (")" * (count))
                    # print(formula)
                else:
                    formula = fam.FamilyTypes[0].Id
                fam_mgr.SetFormula(type_id_param, formula)
                fam_mgr.CurrentType = default_type
                print("\tFormulas set for Id parameters")
        else:
            raise Exception(
                "This shared parameter file does not have the correct group [Identity Data]"
            )

        type_params = forms.select_family_parameters(
            revit.doc, title="Select Family Type Parameters", include_instance=False
        )
        if type_params:
            type_params_names = [x.Definition.Name for x in type_params]
            global_params = forms.select_family_parameters(
                revit.doc,
                title="Select Global Parameters",
                filterfunc=lambda x: x.Definition.Name not in type_params_names,
            )
            if global_params:
                global_params_names = [x.Definition.Name for x in global_params]

    ##### NEED TO CHANGE HOW PARAMETERS ARE BEING ADDED TO FAMILY OBJECT ######
    if type_params_names and global_params_names:
        print("Parameters to be saved")
        print("\tFamily Type Parameters: " + str(type_params_names))
        print("\tGlobal Parameters: " + str(global_params_names))
        for p in params:
            if not p.IsInstance:
                if p.Definition.Name in global_params_names:
                    value = get_value(default_type, p)
                    gp = Parameter(
                        p.Definition.Name,
                        value,
                        DataType=str(p.Definition.ParameterType),
                        ParameterType="Type",
                    )
                    fam.Parameters.append(gp)

        for fam_type, db_type, zO in type_matches:
            # if fam_type.Name == default_name:
            #     ft = FamilyType(fam_type.Name, IsDefault=True)
            # else:
            #     ft = FamilyType(fam_type.Name)
            for p in params:
                if p.Definition.Name in type_params_names:
                    value = get_value(fam_type, p)
                    tp = Parameter(
                        p.Definition.Name,
                        value,
                        DataType=str(p.Definition.ParameterType),
                        ParameterType="Type",
                    )
                    db_type.Parameters.append(tp)

        for i in instance:
            if i.Definition.Name in global_params_names:
                value = get_value(default_type, i)
                ip = Parameter(
                    i.Definition.Name,
                    value,
                    DataType=str(i.Definition.ParameterType),
                    ParameterType="Instance",
                )
                fam.Parameters.append(ip)

    # Save File
    print('Saving Revit family to "{}"'.format(file_path))
    save_ops = DB.SaveAsOptions()
    save_ops.OverwriteExistingFile = True
    save_ops.Compact = True
    revit.doc.SaveAs(file_path, save_ops)
    revit_fam = File(file_path)
    fam.add_files(revit_fam)

    data = fam.to_json()
    # print(data)
    print("Publishing Family")
    client = WebClient()
    client.Headers.Add("Authorization", settings.BIM_HEADERS["Authorization"])
    client.Headers.Add("Accept", "application/json")
    client.Headers.Add("Content-Type", "application/json")
    response = client.UploadString(url, "POST", data)
    response_dict = json.loads(response)
    print("\tSSGFID: {}".format(response_dict["Id"]))
else:
    print("Authorization key needed to run this script")