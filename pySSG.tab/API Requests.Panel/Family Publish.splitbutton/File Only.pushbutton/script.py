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
    params = fam_mgr.Parameters
    ssgfid = [p for p in params if p.Definition.Name == "SSGFID"]

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
                print("Publishing File")
                client = WebClient()
                client.Headers.Add(
                    "Authorization", settings.BIM_HEADERS["Authorization"]
                )
                client.Headers.Add("Accept", "application/json")
                client.Headers.Add("Content-Type", "application/json")
                response = client.UploadString(url, "POST", data)
                response_dict = json.loads(response)
                print("\tSSGFID: {}".format(response_dict["Id"]))

    else:
        raise Exception("This family is missing SSGFID parameter!")

else:
    print("Authorization key needed to run this script")