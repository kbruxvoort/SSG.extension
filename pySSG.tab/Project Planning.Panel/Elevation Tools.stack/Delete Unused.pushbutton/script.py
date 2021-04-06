# pylint: disable=import-error,invalid-name,broad-except
from Autodesk.Revit.DB import *

from pyrevit import revit
from pyrevit import script
from pyrevit import forms


output = script.get_output()
logger = script.get_logger()

viewFamTypes = FilteredElementCollector(revit.doc).OfClass(ViewFamilyType).ToElements()

views = FilteredElementCollector(revit.doc).OfClass(ViewSection).ToElements()

elems = []
for t in viewFamTypes:
    if "Interior Elevation" in Element.Name.GetValue(t):
        elems.append(t)

viewType = elems[0]


for idx, v in enumerate(views):
    if v.GetTypeId() == viewType.Id:
        manufacturer_param_id = ElementId(BuiltInParameter.ALL_MODEL_MANUFACTURER)
        manufacturer_param_prov = ParameterValueProvider(manufacturer_param_id)
        param_begins = FilterStringBeginsWith()
        manufacturer_value_rule = FilterStringRule(
            manufacturer_param_prov, param_begins, "Southwest Solutions Group", False
        )
        filt = ElementParameterFilter(manufacturer_value_rule)
        # filt = ElementCategoryFilter(BuiltInCategory.OST_Rooms)
        collect = FilteredElementCollector(
            revit.doc, v.Id
        ).WhereElementIsNotElementType()
        collect = collect.WherePasses(filt)
        fam = collect.FirstElement()
        # print(fam)
        if not fam:
            with revit.Transaction("Delete Unused Elevation"):
                print('Deleting "%s"' % v.Name)
                revit.doc.Delete(v.Id)

markers = FilteredElementCollector(revit.doc).OfClass(ElevationMarker).ToElements()
count = 0
for marker in markers:
    if marker.CurrentViewCount == 0:
        count += 1
        with revit.Transaction("Delete Unused Markers"):
            revit.doc.Delete(marker.Id)
print("%s Unused Markers Deleted" % str(count))
