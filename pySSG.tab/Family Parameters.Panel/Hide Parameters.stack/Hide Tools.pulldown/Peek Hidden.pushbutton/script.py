import json
import Autodesk.Revit.DB.ExtensibleStorage as es

from pyrevit import revit, script,forms
from extensible_storage import HIDDEN_SCHEMA_GUID

output = script.get_output()
output.resize(960, 640)

schema = es.Schema.Lookup(HIDDEN_SCHEMA_GUID)
if schema:
    entity = revit.doc.OwnerFamily.GetEntity(schema)
    if entity.IsValid():
        value_string = entity.Get[str]("data")
        value_dict = json.loads(value_string)
        table = []
        if value_dict["map"]:
            for k,v in value_dict["map"].items():
                parameter_data = []
                parameter_data.append(k)
                parameter_data.append(v["HiddenName"])
                parameter_data.append(v["HiddenGuid"])
                parameter_data.append(v["ParameterType"])
                parameter_data.append(v["ParameterGroup"])
                table.append(parameter_data)
            
            if table:    
                columns = ['ParameterName', 'HiddenName', 'HiddenGuid', 'Type', 'Original Group']
                output.print_table(
                    table_data=sorted(table, key=lambda x: x[0]),
                    # title="Parameter Map",
                    columns=columns,
                    formats=['', '', '', '']
                )
        else:
            forms.alert("This parameter map has been cleared. Run 'Hide Parameters' to create a new parameter map.")
    else:
        forms.alert("This Family does not contain a parameter map in extensible storage. Run 'Hide Parameters' to create parameter map.")
else:
    forms.alert("Extensible storage schema does not exist. Run 'Hide Parameters' to create schema.")