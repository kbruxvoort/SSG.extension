import json

from pyrevit import revit, DB
from Autodesk.Revit.DB.ExtensibleStorage import SchemaBuilder, AccessLevel, Entity, Schema
from parameters.shared import get_shared_param_by_name

from System import Guid

def create_schema():
    schema_builder = SchemaBuilder(Guid("149f5c9f-45fb-4d6c-a98c-83f6478e9315"))
    schema_builder.SetReadAccessLevel(AccessLevel.Public)
    schema_builder.SetWriteAccessLevel(AccessLevel.Public)
    schema_builder.SetVendorId("kbrux")
    schema_builder.SetSchemaName("ParamTest")
    schema_builder.SetDocumentation("Important documentation from Kyle")

    schema_builder.AddSimpleField("HiddenParameters", str)
    # schema_builder.AddSimpleField("Family", str)
    # schema_builder.AddSimpleField("Type", str)
    # schema_builder.AddSimpleField("Instance", str)
    

    schema = schema_builder.Finish()
    return schema

def add_schema_entity(schema, element, value):
    entity = Entity(schema)
    field = schema.GetField("HiddenParameters")
    entity.Set(field, value)
    element.SetEntity(entity)
    

if __name__ == "__main__":
    # guid = Guid("96a21166-5dcd-43ef-931b-958cff33df64")
    # schema = Schema.Lookup(guid)
    # Schema.EraseSchemaAndAllEntities(schema, False)
    new_schema = create_schema()
    fam = revit.doc.OwnerFamily
    fam_mgr = revit.doc.FamilyManager
    params = fam_mgr.Parameters
    hidden_params = {}
    count = 0
    for p in params:
        if p.IsShared:
            if p.Definition.Visible == False:
                hidden_params[p.Definition.Name] = count
                count += 1 
            
            
        
    # param = get_shared_param_by_name("ACTUAL_Width")
    value = json.dumps(hidden_params)
    with revit.Transaction("add hidden param schema"):
        add_schema_entity(new_schema, fam, value)
    



