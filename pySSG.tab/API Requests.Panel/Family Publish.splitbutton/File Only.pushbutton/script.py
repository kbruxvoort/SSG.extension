import json

from System.Net import WebClient

from pyrevit import revit, forms, DB

from fetchbim.family import Family, FamilyType
from fetchbim import settings
from fetchbim.attributes import Parameter, File

from family_parameters import get_value, get_parameter

if settings.BIM_KEY:

    client = WebClient()
    client.Headers.Add("Authorization", settings.BIM_HEADERS["Authorization"])
    client.Headers.Add("Accept", "application/json")
    client.Headers.Add("Content-Type", "application/json")
    url = settings.POST_FAMILY
    name = revit.doc.Title
    file_path = revit.doc.PathName
    if not file_path:
        file_path = forms.save_file(file_ext="rfa")
    fam_mgr = revit.doc.FamilyManager
    family_types = fam_mgr.Types
    default_type = fam_mgr.CurrentType
    params = fam_mgr.Parameters
    ssgfid = get_parameter("SSGFID", params)

    print("Checking SSGFID")
    if ssgfid:
        # Check ssgfid value
        if ssgfid.IsDeterminedByFormula:
            ssgfid_value = ssgfid.Formula.replace('"', "")
        else:
            ssgfid_value = get_value(default_type, ssgfid)
        if ssgfid_value:
            print("\tSSGFID exists. Finding match in database...")
            get_url = settings.GET_FAMILY.format(ssgfid_value)
            try:
                business_fams = json.loads(client.DownloadString(get_url)).get("BusinessFamilies")[0]
            except SystemError:
                raise Exception("No match for SSGFID. Delete value or find actual match")
            except IndexError:
                raise Exception("No Match! Family probably deleted")
            fam = Family.from_json(business_fams)

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
            print(data)
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
            raise Exception("SSGFID has no value!")
    else:
        raise Exception("This family is missing SSGFID parameter!")

else:
    print("Authorization key needed to run this script")