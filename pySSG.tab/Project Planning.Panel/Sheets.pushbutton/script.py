import math

from pyrevit import revit, script, forms, DB
from packing import *
from rooms import select_placed_rooms


def map_room_views(rooms, views, placed_views):
    grouped_views = {}
    for room in rooms:
        room_views = []
        for view in views:
            if not view.IsTemplate and room.Number in view.Name and view.Id not in placed_views:
                room_views.append(view)
            if room_views:    
                grouped_views[room.Number] = room_views
    return grouped_views

def is_view_valid(view_rect, sheet_width, sheet_height):
    if view_rect.width > sheet_width or view_rect.height > sheet_height:
        return False
    return True



# BORDERS = {'top': .1, 'right': .25, 'bottom': .1, 'left': .1}    

selected_titleblock = forms.select_titleblocks()
if selected_titleblock:

    rooms = select_placed_rooms(revit.doc)
    sheets = DB.FilteredElementCollector(revit.doc).OfCategory(DB.BuiltInCategory.OST_Sheets)
    placed_views = []
    for sheet in sheets:
        placed_views.extend(sheet.GetAllPlacedViews())

    views = (
        DB.FilteredElementCollector(revit.doc)
        .OfCategory(DB.BuiltInCategory.OST_Views)
        .ToElements()
    )

    sort_order = [
        DB.ViewType.FloorPlan,
        DB.ViewType.Elevation,
        DB.ViewType.ThreeD, 
        DB.ViewType.Section,
        # add schedule 
    ]

    grouped_views = map_room_views(rooms, views, placed_views)
    title_offset_x=.25/12
    # title_offset_x=1.0/12
    title_offset_y=1.1/12
    with revit.Transaction("Pack views"):
        for number, views in grouped_views.items():

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
                border_top=.25/12, 
                border_right=2.25/12, 
                border_bottom=.25/12, 
                border_left=.25/12,
            )