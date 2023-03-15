from pyrevit import revit, DB
from Autodesk.Revit.DB.ExtensibleStorage import SchemaBuilder, AccessLevel, Entity, Schema

from System import Guid

def add_schema_entity(schema, element, field, value):
    entity = Entity(schema)
    family_field = schema.GetField("Family")
    type_field = schema.GetField("Type")
    instance_field = schema.GetField("Instance")
    entity.Set(field, value)
    element.SetEntity(entity)
    
if __name__ == "__main__":
    guid = Guid("149f5c9f-45fb-4d6c-a98c-83f6478e9315")
    schema = Schema.Lookup(guid)
    if schema:
        with revit.Transaction("Set Extensible Storage"):
            # fam = revit.pick_element(message='Pick a family')
            fam = revit.doc.OwnerFamily
            fam_mgr = revit.doc.FamilyManager
            current_type = fam_mgr.CurrentType
            # add_schema_entity(schema, fam, schema.GetField("Instance"), "Instance test")
            add_schema_entity(schema, current_type, schema.GetField("Type"), "Type fam doc test")
            add_schema_entity(schema, fam, schema.GetField("Family"), "Fam doc test")