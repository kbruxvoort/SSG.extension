from System import Guid

import Autodesk.Revit.DB.ExtensibleStorage as es


HIDDEN_SCHEMA_GUID = Guid("f5f3b8c9-715b-40e3-a085-c5c3824d36f1")
FETCH_SCHEMA_GUID = Guid("96a21166-5dcd-43ef-931b-958cff33df64")

class ExtensibleSchema:
    def __init__(self, guid=None):
        self.guid = guid
        
    @property
    def schema(self):
        pass

def create_hidden_param_schema():
    builder = es.SchemaBuilder(HIDDEN_SCHEMA_GUID)
    builder.SetReadAccessLevel(es.AccessLevel.Public)
    builder.SetWriteAccessLevel(es.AccessLevel.Public)
    builder.SetVendorId("pySSG")
    builder.SetSchemaName("HiddenParameters")
    builder.SetDocumentation(
        "This schema is used to map visible family parameters to a shared hidden parameter."
    )
    field_builder = builder.AddSimpleField("data", str)
    schema = builder.Finish()
    return schema

def add_schema_entity(schema, element, field_name, value):
    entity = es.Entity(schema)
    field = schema.GetField(field_name)
    entity.Set(field, value)
    element.SetEntity(entity)