import os
import re
import json
import base64
import requests

import Autodesk.Revit.DB.ExtensibleStorage as es

from System import Guid
from pyrevit import forms, script
from parameters.family import get_value
from extensible_storage import FETCH_SCHEMA_GUID

TOKEN_REGEX = re.compile(r'^[a-zA-Z0-9_-]+\.[a-zA-Z0-9_-]+\.[a-zA-Z0-9_-]+$')

def validate_token(token):
    return TOKEN_REGEX.match(token)

def validate_string(token_string):
    url = "https://www.ssgbim.com/api/Home/Family/b3d9f8ca-2564-4c1b-b192-3ac22fcdb86d"
    headers = {
        "Authorization": "Bearer {}".format(token_string),
        "Content-Type": "application/json",
    }
    response = requests.get(url, headers=headers)
    return response.ok
    
    
def get_auth():
    bim_key = os.environ.get("BIM_KEY")
    if not bim_key:
        my_config = script.get_config("BIM_KEY")
        bim_key = my_config.get_option("token", "")
        if not bim_key:
            string = forms.ask_for_string(
                title="'BIM_KEY not found in environment variables",
                prompt="Enter Fetch API Token"
            )
            if string:
                if validate_string(string) is True:
                    bim_key = string
                    my_config.token = string
                    script.save_config()
                    save_key = forms.alert(
                        warn_icon=False,
                        yes=True,
                        no=True,
                        ok=False,
                        msg="Would you like to save token to environment variables?"
                    )
                    if save_key:
                        os.environ["BIM_KEY"] = bim_key
                        forms.alert(
                            msg="Your computer may require a restart for environment variable to be read.",
                            cancel=False
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
        fam_id = get_value(param, current_type)
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

