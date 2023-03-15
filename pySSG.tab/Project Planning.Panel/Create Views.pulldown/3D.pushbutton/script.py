"""
This script creates individual 3D views for each room in the active view. The active view must be a 3D view.
"""

# pylint: disable=import-error,invalid-name,broad-except
import clr

# Import RevitAPI
clr.AddReference("RevitAPI")
import Autodesk
from Autodesk.Revit.DB import *

from pyrevit import revit
from pyrevit import script
from pyrevit import forms

__title__ = " 3D Room Views by Active 3D View"
__author__ = "{{author}}"
# __context__ = "active-3d-view"

logger = script.get_logger()
output = script.get_output()

threeD_view = revit.doc.ActiveView

forms.check_viewtype(threeD_view, ViewType.ThreeD, exitscript=True)

rooms = []
collector = (
    FilteredElementCollector(revit.doc)
    .OfCategory(BuiltInCategory.OST_Rooms)
    .ToElements()
)
for c in collector:
    if c.Area != 0:
        rooms.append(c)

views = []
col2 = FilteredElementCollector(revit.doc).OfClass(View3D).ToElements()
for view in col2:
    if view.IsTemplate == False:
        views.append(view.Name)


total_work = len(rooms)
for idx, room in enumerate(rooms):
    roomName = room.LookupParameter("Name").AsString()
    roomNumber = room.LookupParameter("Number").AsString()
    newName = "3D - " + roomName + " " + roomNumber

    # Get View Family Type of Plan
    viewTypeId = threeD_view.GetTypeId()
    level = room.LevelId

    with revit.Transaction("Create 3D Views by Room"):
        if newName not in views:
            # Get Room Bounding Box and Create New
            roomBB = room.get_BoundingBox(threeD_view)
            rMax = roomBB.Max
            rMin = roomBB.Min
            newMaxP = XYZ(rMax.X + 1, rMax.Y + 1, rMax.Z + 1)
            newMinP = XYZ(rMin.X - 1, rMin.Y - 1, rMin.Z - 1)
            newBB = BoundingBoxXYZ()
            newBB.Max = newMaxP
            newBB.Min = newMinP

            threeD = View3D.CreateIsometric(revit.doc, viewTypeId)
            # box = app.Create.NewBoundingBoxXYZ()
            # box.Min = Min[count]
            # box.Max = Max[count]
            # bbox.append(box)
            a = View3D.SetSectionBox(threeD, newBB)
            threeD.Name = newName
            print("Creating 3D View: %s" % threeD.Name)

        else:
            message = 'View "%s" already exists' % newName
            logger.warning(message)
        output.update_progress(idx + 1, total_work)
print("Completed\n")
