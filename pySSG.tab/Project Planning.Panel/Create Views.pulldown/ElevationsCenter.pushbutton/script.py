from pyrevit import revit, DB, forms
from rooms import select_placed_rooms, get_number, get_name, get_center

from Autodesk.Revit import Exceptions

elevation_type_id = revit.doc.GetDefaultElementTypeId(
    DB.ElementTypeGroup.ViewTypeElevation
)

view_names = []
elevation_views = DB.FilteredElementCollector(revit.doc).OfClass(DB.ViewSection).ToElements()
for view in elevation_views:
    if view.IsTemplate == False:
        view_names.append(view.Name)
        
rooms = select_placed_rooms(revit.doc, active_view_only=True)

if rooms:

    max_value = len(rooms)

    with revit.Transaction("Create Elevations"):
        with forms.ProgressBar() as pb:
            for count, room in enumerate(rooms, start=1):
                new_name = "Elevation - {} - {} - ".format(get_number(room), get_name(room))

                room_center = get_center(room)

                elevation_marker = DB.ElevationMarker.CreateElevationMarker(
                    revit.doc, elevation_type_id, room_center, 100
                )
                directions = ["West", "North", "East", "South"]
                for i, direction in enumerate(directions):
                    elevation = elevation_marker.CreateElevation(
                        revit.doc, revit.doc.ActiveView.Id, i
                    )
                    elevation_name = new_name + direction
                    try:
                        revit.update.set_name(elevation, elevation_name)
                    except Exceptions.ArgumentException:
                        print("View Name '{}' already exists.".format(elevation_name))
                pb.update_progress(count, max_value)