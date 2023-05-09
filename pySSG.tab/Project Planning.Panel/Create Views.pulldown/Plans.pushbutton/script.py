from pyrevit import revit, DB, forms
from rooms import select_placed_rooms, get_name, get_number, create_expanded_bounding_box


plan_type_id = revit.doc.GetDefaultElementTypeId(
    DB.ElementTypeGroup.ViewTypeFloorPlan
)
default_tag_id = revit.doc.GetDefaultFamilyTypeId(
    DB.ElementId(DB.BuiltInCategory.OST_RoomTags)
)

view_names = []
plan_views = DB.FilteredElementCollector(revit.doc).OfClass(DB.ViewPlan).ToElements()
for view in plan_views:
    if view.IsTemplate == False:
        view_names.append(view.Name)


rooms = select_placed_rooms(revit.doc)

if rooms:
    max_value = len(rooms)
    with revit.Transaction("Create floor plans by room"):
        with forms.ProgressBar() as pb:
            for count, room in enumerate(rooms, start=1):

                new_name = "Floor Plan - {} - {}".format(get_number(room), get_name(room))
                if new_name not in view_names:
                    created_view = DB.ViewPlan.Create(revit.doc, plan_type_id, room.LevelId)
                    new_bounding_box = create_expanded_bounding_box(room)

                    # Set the new Bounding Box
                    created_view.CropBoxActive = True
                    created_view.CropBoxVisible = False
                    created_view.CropBox = new_bounding_box
                    annotation_crop_parameter = created_view.get_Parameter(
                        DB.BuiltInParameter.VIEWER_ANNOTATION_CROP_ACTIVE
                    )
                    annotation_crop_parameter.Set(True)

                    # Name the New View
                    created_view.Name = new_name
                    linked_room_id = DB.LinkElementId(room.Id)
                    location = DB.UV(
                        room.Location.Point.X, 
                        room.Location.Point.Y
                    )
                    room_tag = revit.doc.Create.NewRoomTag(linked_room_id, location, created_view.Id)
                else:
                    print("{} already exists in project".format(new_name))
                pb.update_progress(count, max_value)