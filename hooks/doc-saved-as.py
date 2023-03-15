import os

from Autodesk.Revit.DB.Events import RevitAPIEventStatus

from pyrevit import forms, EXEC_PARAMS
from fetch_client import Client, get_family_id, file_from_path, get_auth


if EXEC_PARAMS.event_args.Status == RevitAPIEventStatus.Succeeded:
    doc = EXEC_PARAMS.event_args.Document
    if doc.IsFamilyDocument:
        BIM_KEY = get_auth()
        if BIM_KEY:
            ssgfid = get_family_id(doc)
            if ssgfid:
                fetch = Client(auth=BIM_KEY)
                r = fetch.families.retrieve(ssgfid)
                if r:
                    result = forms.alert(
                        msg="This family has a valid SSGFID. Would you like to save to database object '{}'?".format(r.get('Name')),
                        title="Save family to database",
                        yes=True,
                        no=True,
                        ok=False,
                        warn_icon=False 
                    )
                    if result:
                        file_data = file_from_path(doc.PathName)
                        file_name, extension = doc.PathName.split("\\")[-1].split(".")
                        data={
                            "FamilyId": ssgfid,
                            "Files": [
                                {
                                    "FileId": None,
                                    "FileName": file_name,
                                    "FileExtension": "." + extension,
                                    "FileKey": "FamilyRevitFile",
                                    "FileData": file_data
                                }
                            ]
                        }
                        r2 = fetch.families.update(data=data)
                        if r2:
                            forms.alert(
                                msg="Successfully saved '{}'".format(file_name + "." + extension),
                                warn_icon=False
                                )

