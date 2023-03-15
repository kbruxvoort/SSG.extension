from System import Guid

import Autodesk.Revit.DB.ExtensibleStorage as es


HIDDEN_SCHEMA_GUID = Guid("f5f3b8c9-715b-40e3-a085-c5c3824d36f1")
FETCH_SCHEMA_GUID = Guid("96a21166-5dcd-43ef-931b-958cff33df64")


def create_schema():
    schema_builder = es.SchemaBuilder(Guid("149f5c9f-45fb-4d6c-a98c-83f6478e9315"))
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