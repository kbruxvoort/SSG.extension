import json

from System.Net import WebClient

from pyrevit import revit, forms, DB

from fetchbim.family import Family, FamilyType
from fetchbim import settings
from fetchbim.attributes import Parameter, File

from family_parameters import get_value, get_parameter

# Accessing shared parameters
app = revit.doc.Application
sharedParametersFile = app.OpenSharedParameterFile()
sharedGroups = sharedParametersFile.Groups

# SSGFID & SSGTID Parameters
id_group = [group.Definitions for group in sharedGroups if group.Name == "Identity Data"]
if not id_group:
    raise Exception('This shared file has no group "Identity Data"')
group_definitions = id_group[0]
ssgfid_param = [x for x in group_definitions if x.Name == "SSGFID"]
ssgtid_param = [x for x in group_definitions if x.Name == "SSGTID"]

# zO Parameter
other_group = [group.Definitions for group in sharedGroups if group.Name == "Other"]
if not other_group:
    raise Exception('This shared file has no group "Other"')
other_definitions = other_group[0]
zO_param = [x for x in other_definitions if x.Name == "zO"]


if settings.BIM_KEY:
    # Client settings
    client = WebClient()
    client.Headers.Add("Authorization", settings.BIM_HEADERS["Authorization"])
    client.Headers.Add("Accept", "application/json")
    client.Headers.Add("Content-Type", "application/json")
    url = settings.POST_FAMILY

    # Family data
    file_path = revit.doc.PathName
    if not file_path:
        file_path = forms.save_file(file_ext="rfa")
    name = revit.doc.Title
    fam_mgr = revit.doc.FamilyManager
    family_types = [t for t in fam_mgr.Types if t.Name != " "]
    default_type = fam_mgr.CurrentType
    default_name = default_type.Name
    owner_fam = revit.doc.OwnerFamily
    category = owner_fam.FamilyCategory.Name
    params = fam_mgr.Parameters
    instance = [p for p in params if p.IsInstance]

    ssgfid = get_parameter("SSGFID", params)
    ssgtid = get_parameter("SSGTID", params)
    zO = get_parameter("zO", params)

    type_params_names, global_params_names = [], []

    # Shell family
    start_fam = Family(name, CategoryName=category)

    print("Checking Parameters")
    if ssgfid is None:
        with revit.Transaction("Add SSGFID Parameter"):
            print("\tAdding SSGFID")
            ssgfid = fam_mgr.AddParameter(ssgfid_param[0], DB.BuiltInParameterGroup.PG_IDENTITY_DATA, False)
    if ssgtid is None:
        with revit.Transaction("Add SSGTID Parameter"):
            print("\tAdding SSGTID")
            ssgtid = fam_mgr.AddParameter(ssgtid_param[0], DB.BuiltInParameterGroup.PG_IDENTITY_DATA, False)
    if zO is None:
        with revit.Transaction("Add zO Parameter"):
            print("\tAdding zO")
            zO = fam_mgr.AddParameter(zO_param[0], DB.BuiltInParameterGroup.INVALID, False)

    # Check ssgfid value
    if ssgfid.IsDeterminedByFormula:
        ssgfid_value = ssgfid.Formula.replace('"', "")
    else:
        ssgfid_value = get_value(default_type, ssgfid)

    # Pull data from database if there is a match
    if ssgfid_value:
        print("\tSSGFID exists. Finding match in database...")
        get_url = settings.GET_FAMILY.format(ssgfid_value)
        try:
            business_fams = json.loads(client.DownloadString(get_url)).get("BusinessFamilies")[0]
        except SystemError:
            raise Exception("No match for SSGFID. Delete value or find actual match")
        fam = Family.from_json(business_fams)
        fam.Name = name
        print("\tMatch Found: {}".format(fam))
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
        print("\tSSGFID has no value")
        # Add types to shell family
        for fam_type in family_types:
            if fam_type.Name == default_name:
                ft = FamilyType(fam_type.Name, IsDefault=True)
            else:
                ft = FamilyType(fam_type.Name)
            start_fam.FamilyTypes.append(ft)

        shell_data = start_fam.to_json()
        response = client.UploadString(url, "POST", shell_data)
        fam_json = json.loads(response)
        fam = Family.from_json(fam_json)
        print("\t[{}] Shell Family Created".format(fam.Id))

        with revit.Transaction("Set Identity Formulas"):
            # Set SSGFID
            fam_mgr.SetFormula(ssgfid, '"{}"'.format(fam.Id))
            # Set SSGTID and zO
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
                            # Set zO Value
                            fam_mgr.Set(zO, count)
                            formula += 'if(zO = {}, "{}", '.format(count, db_type.Id)
                            type_matches.append((revit_type, db_type, count))
                            # break
                formula = formula + '"ERROR"' + (")" * (count))
                fam_mgr.SetFormula(ssgtid, formula)
                fam_mgr.CurrentType = default_type
            elif len(fam.FamilyTypes) == 1:
                fam_mgr.Set(zO, 1)
                formula = '"{}"'.format(fam.FamilyTypes[0].Id)
                fam_mgr.SetFormula(ssgtid, formula)
                type_matches = [(family_types[0], fam.FamilyTypes[0], 1)]
            else:
                raise Exception("Family must have at least 1 type")

            print("\tFormulas set for Id parameters")

    # Select parameters to sync to database
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
    else:
        global_params = forms.select_family_parameters(
            revit.doc,
            title="Select Global Parameters",
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
    fam.Files = []
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