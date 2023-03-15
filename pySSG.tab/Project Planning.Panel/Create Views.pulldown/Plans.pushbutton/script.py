# pylint: disable=import-error,invalid-name,broad-except
import clr

# Import RevitAPI
clr.AddReference("RevitAPI")
import Autodesk
from Autodesk.Revit.DB import *

from pyrevit import revit
from pyrevit import script
from pyrevit import forms


logger = script.get_logger()
output = script.get_output()

plan = revit.doc.ActiveView

# forms.check_viewtype(plan, ViewType.FloorPlan, exitscript=True)

room_tags = (
    FilteredElementCollector(revit.doc, revit.doc.ActiveView.Id)
    .OfCategory(BuiltInCategory.OST_RoomTags)
    .WhereElementIsNotElementType()
    .ToElements()
)
if room_tags:
    room_tag = room_tags[0]

views = []
col2 = FilteredElementCollector(revit.doc).OfClass(ViewPlan).ToElements()
for view in col2:
    if view.IsTemplate == False:
        views.append(view.Name)


filter = Architecture.RoomFilter()
collector = (
    FilteredElementCollector(revit.doc, plan.Id).WherePasses(filter).ToElements()
)

total_work = len(collector)
for idx, room in enumerate(collector):
    roomName = room.LookupParameter("Name").AsString()
    roomNumber = room.LookupParameter("Number").AsString()
    newName = "Floor Plan - " + roomName + " " + roomNumber

    # Get View Family Type of Plan
    viewTypeId = plan.GetTypeId()
    level = room.LevelId
    with revit.Transaction("Create Plans by Room"):
        if newName not in views:
            # Create View
            roomView = ViewPlan.Create(revit.doc, viewTypeId, level)

            # Get Room Bounding Box and Create New
            roomBB = room.get_BoundingBox(plan)
            rMax = roomBB.Max
            rMin = roomBB.Min
            newMaxP = XYZ(rMax.X + 1, rMax.Y + 1, rMax.Z)
            newMinP = XYZ(rMin.X - 1, rMin.Y - 1, rMin.Z)
            newBB = BoundingBoxXYZ()
            newBB.Max = newMaxP
            newBB.Min = newMinP

            # Set the new Bounding Box
            roomView.CropBoxActive = True
            roomView.CropBoxVisible = False
            roomView.CropBox = newBB
            aCrop = roomView.get_Parameter(
                BuiltInParameter.VIEWER_ANNOTATION_CROP_ACTIVE
            )
            aCrop.Set(True)

            # Name the New View

            roomView.Name = newName
            print("Creating plan: %s" % roomView.Name)

        else:
            message = 'View "%s" already exists' % newName
            logger.warning(message)

        try:
        #     # Find Center of Room and Move it
            roomId = LinkElementId(room.Id)
        #     bbox = roomView.CropBox
        #     XYZLocation = (bbox.Max + bbox.Min) / 2.0
            
            # location = Autodesk.Revit.DB.UV(XYZLocation.X, XYZLocation.Y)
            current = room.Location.Point
            location = Autodesk.Revit.DB.UV(current.X, current.Y)
        #     newloc = XYZLocation - current
        #     room.Location.Move(newloc)

        #     # Tag Room
            roomTag = revit.doc.Create.NewRoomTag(roomId, location, roomView.Id)
            # roomTag = revit.doc.Create.NewRoomTag(roomId, location, roomView.Id)
            # roomTag.RoomTagType = room_tag.RoomTagType
        #     # print("-Tagging Room")
        except Exception as e:
            message = 'Room tag for "%s" already exists' % roomName
            logger.warning(e)
            continue
        output.update_progress(idx + 1, total_work)
print("Completed\n")