import os
import re
import json
import base64

import Autodesk.Revit.DB.ExtensibleStorage as es

from System import Guid
from pyrevit import forms
from parameters.family import get_value
from extensible_storage import FETCH_SCHEMA_GUID

TOKEN_REGEX = re.compile(r'^[a-zA-Z0-9_-]+\.[a-zA-Z0-9_-]+\.[a-zA-Z0-9_-]+$')

def validate_token(token):
    return TOKEN_REGEX.match(token)
    
    
def get_auth():
    bim_key = os.environ["BIM_KEY"]
    if not bim_key:
        string = forms.ask_for_string(
            title="'BIM_KEY not found in environment variables",
            prompt="Enter Fetch API Token"
        )
        if validate_token(string):
            bim_key = string
            forms.alert(
                warn_icon=False,
                yes=True,
                no=True,
                ok=False,
                msg="Would you like to save token to environment variables?"
            )
        else:
            forms.alert(
                msg="token is not valid",
                exitscript=True
                )
    return bim_key


def is_guid(guid_string):
    pattern = r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$'
    match = re.match(pattern, guid_string)
    return bool(match)


def get_storage_id(family_document):
    schema = es.Schema.Lookup(FETCH_SCHEMA_GUID)
    if schema:
        entity = family_document.OwnerFamily.GetEntity(schema)
        if entity.IsValid():
            value_string = entity.Get[str]("Data")
            value_dict = json.loads(value_string)
            if value_dict:
                fam_id = value_dict.get("ID")
                if is_guid(fam_id):
                    return fam_id


def get_param_id(family_document):
    current_type = family_document.FamilyManager.CurrentType
    param = family_document.FamilyManager.get_Parameter(Guid("cd2bd688-6eb7-4586-ba8c-148a0d1c845c"))
    if param:
        fam_id = get_value(current_type, param)
        if is_guid(fam_id):
            return fam_id
    

def get_family_id(family_document):
    return get_param_id(family_document) or get_storage_id(family_document)
        

def file_from_path(file_path):
        try:
            with open(file_path, "rb") as file:
                byteform = base64.b64encode(file.read())
                return byteform.decode("utf-8")
        except TypeError as e:
            print("File path is incorrect: {}".format(e))

