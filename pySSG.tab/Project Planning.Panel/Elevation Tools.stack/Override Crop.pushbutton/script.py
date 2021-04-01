"""Override the line weight of the cropbox of interior elevations."""
#pylint: disable=import-error,invalid-name,broad-except

from Autodesk.Revit.DB import *

from pyrevit import revit
from pyrevit import script
from pyrevit import forms

__title__ = "Override Elevation Cropbox"
__author__ = "{{author}}"

output = script.get_output()
logger = script.get_logger()
 
lineWeight = 5

ogs = OverrideGraphicSettings().SetProjectionLineWeight(lineWeight)

viewFamTypes = FilteredElementCollector(revit.doc).OfClass(ViewFamilyType).ToElements()

views = FilteredElementCollector(revit.doc).OfClass(ViewSection).ToElements()

elems = []
for t in viewFamTypes:
    if "Interior Elevation" in Element.Name.GetValue(t):
        elems.append(t)

viewType = elems[0]

with revit.Transaction("Override Crop Lineweight"):
    for v in views:
        if v.GetTypeId() == viewType.Id:
            cropId = ElementId(int(v.Id.ToString())-1)
            v.CropBoxActive = True
            v.CropBoxVisible = True
            v.SetElementOverrides(cropId, ogs)
