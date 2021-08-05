#pylint: disable=import-error,invalid-name,broad-except
from pyrevit import revit, DB
from pyrevit import script


output = script.get_output()
logger = script.get_logger()


filt = DB.ElementCategoryFilter(DB.BuiltInCategory.OST_RoomTags)
collect = DB.FilteredElementCollector(revit.doc, revit.doc.ActiveView.Id).WhereElementIsNotElementType()
collect = collect.WherePasses(filt).ToElements()

categories = [DB.BuiltInCategory.OST_Rooms]
rooms = [x for x in revit.query.get_elements_by_categories(categories) if x.Area > 0]

if rooms:
    with revit.Transaction("Center Rooms"):
        for room in rooms:
            bbox = room.get_BoundingBox(revit.doc.ActiveView)
            center = (bbox.Max + bbox.Min) / 2.0
            location = DB.UV(center.X, center.Y)
            current_room = room.Location.Point
            new_loc = center - current_room
            room.Location.Move(new_loc)


        if collect:
            with revit.Transaction("Center Tags"):
                for room_tag in collect:
                    room = room_tag.Room
                    bbox = room.get_BoundingBox(revit.doc.ActiveView)
                    center = (bbox.Max + bbox.Min) / 2.0
                    location = DB.UV(center.X, center.Y)
                    current_room = room.Location.Point
                    current_tag = room_tag.Location.Point
                    new_loc = center - current_tag
                    room_tag.Location.Move(new_loc)
    
