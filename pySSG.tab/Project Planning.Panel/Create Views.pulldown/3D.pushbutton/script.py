from pyrevit import revit, DB, forms
from rooms import select_placed_rooms, get_number, get_name, create_expanded_bounding_box


threeD_type_id = revit.doc.GetDefaultElementTypeId(
    DB.ElementTypeGroup.ViewType3D
)

view_names = []
threeD_views = DB.FilteredElementCollector(revit.doc).OfClass(DB.View3D).ToElements()
for view in threeD_views:
    if view.IsTemplate == False:
        view_names.append(view.Name)


rooms = select_placed_rooms(revit.doc)

if rooms:
    max_value = len(rooms)
    with revit.Transaction("Create floor plans by room"):
        with forms.ProgressBar() as pb:
            for count, room in enumerate(rooms, start=1):
                new_name = "3D - {} - {}".format(get_number(room), get_name(room))
                if new_name not in view_names:
                    created_view = DB.View3D.CreateIsometric(revit.doc, threeD_type_id)
                    new_bounding_box = create_expanded_bounding_box(room, z=(-1,0))
                    
                    # Set the new Bounding Box
                    created_view.SetSectionBox(new_bounding_box)

                    # Name the New View
                    created_view.Name = new_name
                else:
                    print("{} already exists in project".format(new_name))
                pb.update_progress(count, max_value)