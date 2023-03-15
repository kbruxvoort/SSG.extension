from pyrevit import DB, revit
from System import Guid

# returns all FamilyInstances
c0 = (
    DB.FilteredElementCollector(revit.doc)
    .OfClass(DB.FamilyInstance)
    .ToElements()
)

# returns all Families
c1 = (
    DB.FilteredElementCollector(revit.doc)
    .OfClass(DB.Family)
    .ToElements()
)

# returns FamilyInstances that contain shared parameter SSGTID
filter_rule = DB.SharedParameterApplicableRule("SSGTID")
filt = DB.ElementParameterFilter(filter_rule)
c2 = DB.FilteredElementCollector(revit.doc).WherePasses(filt).ToElements()

# returns FamilyInstances with manufacturer parameter value containing SSG
# can switch FamilySymbols if you change to WhereElementIsElementType
mfg_param_id = DB.ElementId(DB.BuiltInParameter.ALL_MODEL_MANUFACTURER)
mfg_param_prov = DB.ParameterValueProvider(mfg_param_id)
param_contains = DB.FilterStringContains()
mfg_value_rule = DB.FilterStringRule(
    mfg_param_prov,
    param_contains,
    "Southwest Solutions Group",
    False
)
param_filter = DB.ElementParameterFilter(mfg_value_rule)
c3 = (
    DB.FilteredElementCollector(revit.doc)
    .WherePasses(param_filter)
    .WhereElementIsNotElementType()
    .ToElements()
)

# Returns Families (since it is attached at family level) with extensible storage schema
schema_guid = Guid("96a21166-5dcd-43ef-931b-958cff33df64")
extensible_filter = DB.ExtensibleStorage.ExtensibleStorageFilter(schema_guid)
c4 = (
    DB.FilteredElementCollector(revit.doc)
    .WherePasses(extensible_filter)
    .ToElements()
)


for c in c2:
    print("{}: {}".format(type(c), c.Name))