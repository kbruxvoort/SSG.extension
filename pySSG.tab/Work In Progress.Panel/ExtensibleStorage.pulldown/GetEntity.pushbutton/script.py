import json

from pyrevit import revit, DB
from Autodesk.Revit.DB.ExtensibleStorage import SchemaBuilder, AccessLevel, Entity, Schema, Field
from Autodesk.Revit.Exceptions import InvalidOperationException

from System import Guid

def get_schema_entity(schema, element):
    entity = element.GetEntity(schema)
    if entity.IsValid():
        # data = entity.Get[str]("Data")
        # new_data = "\n\t".join([x.strip() for x in data.split(",")])
        # print("Data:\n\t{}".format(new_data))
        param_string = entity.Get[str]("HiddenParameters")
        # print(param_string)
        param_dict = json.loads(param_string)
        # print(param_dict)
        # print(type(param_dict))
        for k,v in param_dict.items():
            print(k, v)
        # print("Family: {}".format(entity.Get[str]("HiddenParameters")))
        # print("Family: {}".format(entity.Get[Field](field)))
    else:
        print("No entity found")
    
    
if __name__ == "__main__":
    guid = Guid("149f5c9f-45fb-4d6c-a98c-83f6478e9315")
    # guid = Guid("96a21166-5dcd-43ef-931b-958cff33df64")
    schema = Schema.Lookup(guid)
    if schema:
        # fam = revit.pick_element(message='Pick a family')
        fam = revit.doc.OwnerFamily
        get_schema_entity(schema, fam)
        # for fam_type_id in fam.GetValidTypes():
        #     fam_type = revit.doc.GetElement(fam_type_id)
        #     get_schema_entity(schema, fam_type)