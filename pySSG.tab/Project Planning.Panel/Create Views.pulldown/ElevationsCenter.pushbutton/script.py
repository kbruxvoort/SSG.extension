#pylint: disable=import-error,invalid-name,broad-except
import clr
import math
# Import RevitAPI
clr.AddReference("RevitAPI")
import Autodesk
from Autodesk.Revit.DB import *
from Autodesk.Revit.Exceptions import ArgumentException

from pyrevit import revit
from pyrevit import script
from pyrevit import forms


# forms.check_viewtype(revit.doc.ActiveView, ViewType.FloorPlan, exitscript=True)

logger = script.get_logger()
output = script.get_output()

class RoomOption(forms.TemplateListItem):
    # def __init__(self, room_element):
    #     super(RoomOption, self).__init__(room_element)

    @property
    def name(self):
        """Room name."""
        return '%s' % revit.query.get_name(self.item)

rooms, elems= [], []

col1 = FilteredElementCollector(revit.doc).OfCategory(BuiltInCategory.OST_Rooms).ToElements()

col2 = FilteredElementCollector(revit.doc).OfClass(ViewFamilyType).ToElements()


for v in col2:
    if "Interior Elevation" in Element.Name.GetValue(v):
        elems.append(v)

viewType = elems[0]

for room in col1:
    if room.Area != 0:
        rooms.append(room)


res = forms.SelectFromList.show(
                                sorted([RoomOption(x) for x in rooms],
                                       key=lambda x: x.Number),
                                multiselect=True,
                                # name_attr= 'Number',
                                button_name='Select Rooms')

total_work = len(res)
with revit.Transaction("Create Elevations"):
    for idx, r in enumerate(res):
        roomName = r.LookupParameter("Name").AsString().upper()
        roomNumber = r.LookupParameter("Number").AsString()
        bbox = r.get_BoundingBox(revit.doc.ActiveView)
        rMin = bbox.Min
        rMax = bbox.Max
        roomCenter = (rMin + rMax)/2.0

        eleMarker = ElevationMarker.CreateElevationMarker(revit.doc, viewType.Id, roomCenter, 100)
        ele1 = eleMarker.CreateElevation(revit.doc, revit.doc.ActiveView.Id, 1)
        ele2 = eleMarker.CreateElevation(revit.doc, revit.doc.ActiveView.Id, 2)
        ele3 = eleMarker.CreateElevation(revit.doc, revit.doc.ActiveView.Id, 3)
        ele4 = eleMarker.CreateElevation(revit.doc, revit.doc.ActiveView.Id, 0)
        newName = "ELEVATION - " + roomName + " " + roomNumber + " - "
        # print(newName)
        
        try:
            print('Creating Elevations for  "%s - %s"' % (roomNumber, roomName))
            ele1.Name = newName + "NORTH"
            ele2.Name = newName + "EAST"
            ele3.Name = newName + "SOUTH"
            ele4.Name = newName + "WEST"

        except ArgumentException:
            message = 'View Name already exists.'
            logger.warning(message)

        output.update_progress(idx + 1, total_work)
        
print("Completed\n")
    
