import os

from pyrevit import revit, HOST_APP
from parameters.shared import SharedParameterFile

from fetch_client import Client

auth = os.environ.get('BIM_KEY')
fetch = Client(auth=auth)

all_fams = fetch.families.list()
all_files = fetch.files.list()
all_rules = fetch.rules.list()

print("{} families".format(len(all_fams)))
print("{} files".format(len(all_files)))
print("{} rules".format(len(all_rules)))


# app = HOST_APP.app
# spf = SharedParameterFile().set_file()

# print(spf.file.Filename)

# param_guid = "dbb4909b-e801-44d0-a534-c429fdf4c415"

# groups = spf.file.Groups
# for g in groups:
#     print(g.Definitions.get_Item(param_guid))
# spf.file.Groups.get_Item(Guid(param_guid))
    