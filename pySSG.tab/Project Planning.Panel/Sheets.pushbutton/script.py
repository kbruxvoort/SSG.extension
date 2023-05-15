import math

from pyrevit import revit, script, forms, DB
from packing import *
from rooms import select_placed_rooms, get_name, get_number


def map_room_views(rooms, views, placed_views):
    grouped_views = {}
    for room in rooms:
        room_name = get_name(room)
        room_number = get_number(room)
        number_name = "{} - {}".format(room_number, room_name)
        room_views = []
        # rooms_views = list(filter(view_filter, views))
        for view in views:
            # print(view.Name)
            if not view.IsTemplate and room_number in view.Name and view.Id not in placed_views and view.ViewType != DB.ViewType.Schedule:
                room_views.append(view)
            if room_views:    
                grouped_views[number_name] = room_views
    return grouped_views


 

selected_titleblock = forms.select_titleblocks()
if selected_titleblock:

    rooms = select_placed_rooms(revit.doc)
    sheets = DB.FilteredElementCollector(revit.doc).OfCategory(DB.BuiltInCategory.OST_Sheets)
    placed_views = []
    for sheet in sheets:
        placed_views.extend(sheet.GetAllPlacedViews())

    views = revit.query.get_all_views(include_nongraphical=False)

    grouped_views = map_room_views(rooms, views, placed_views)
    title_offset_x=.25/12
    title_offset_y=.75/12
    with revit.Transaction("Pack views"):
        for number_name, views in grouped_views.items():

            view_rectangles = [Rectangle(
                v, 
                width=v.Outline.Max.U - v.Outline.Min.U + title_offset_x, 
                height=v.Outline.Max.V - v.Outline.Min.V + title_offset_y
            )
                for v in views]
            
            view_rectangles.sort(key=lambda v: (v.height, v.width), reverse=True)
            
            sheets = pack_views(
                revit.doc,
                view_rectangles, 
                selected_titleblock,
                sheet_name=number_name,   
                border_top=.25/12, 
                border_right=2.25/12, 
                border_bottom=.5/12, 
                border_left=.5/12,
                draw_cut_lines=False
            )