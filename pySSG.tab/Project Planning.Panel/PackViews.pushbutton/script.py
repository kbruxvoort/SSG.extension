from pyrevit import revit, forms, DB
from packing import Rectangle, pack_views

  
def view_filter(view, placed_views):
    acceptable_types = [
        DB.ViewType.FloorPlan,
        DB.ViewType.CeilingPlan,
        DB.ViewType.Elevation,
        DB.ViewType.ThreeD,
        DB.ViewType.AreaPlan,
        DB.ViewType.Section,
        DB.ViewType.Detail,
        DB.ViewType.Rendering,
        DB.ViewType.Schedule
    ]
    return not view.IsTemplate \
           and view.Id not in placed_views \
           and view.ViewType in acceptable_types 

selected_titleblock = forms.select_titleblocks()
if selected_titleblock:

    sheets = DB.FilteredElementCollector(revit.doc).OfCategory(DB.BuiltInCategory.OST_Sheets)
    placed_views = []
    for sheet in sheets:
        placed_views.extend(sheet.GetAllPlacedViews())


    selected_views = forms.select_views(filterfunc=lambda v: view_filter(v, placed_views))

    title_offset_x=.25/12
    title_offset_y=.75/12
    
    if selected_views:
        with revit.Transaction("Pack views"):
            view_rectangles = [Rectangle(
                v, 
                width=v.Outline.Max.U - v.Outline.Min.U + title_offset_x, 
                height=v.Outline.Max.V - v.Outline.Min.V + title_offset_y
            )
                for v in selected_views]
            
            view_rectangles.sort(key=lambda v: (v.height, v.width), reverse=True)
            
            sheets = pack_views(
                revit.doc,
                view_rectangles, 
                selected_titleblock,
                sheet_name=None,   
                border_top=.25/12, 
                border_right=2.25/12, 
                border_bottom=.5/12, 
                border_left=.5/12,
                draw_cut_lines=False
            )