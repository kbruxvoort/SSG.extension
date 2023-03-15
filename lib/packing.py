from pyrevit import revit, DB

def sort_views(views, view_type_order):
    def key_function(view):
        view_type_index = view_type_order.index(view.ViewType) if view.ViewType in view_type_order else len(view_type_order)
        width = view.Outline.Max.U - view.Outline.Min.U
        height = view.Outline.Max.V - view.Outline.Min.V
        area = width * height
        return (view_type_index, -area)
    return sorted(views, key=key_function)

        
# def pack_views_to_sheet(views, sheet, start_point=(0, 0), spacing=1.0):
#     x, y = start_point
#     sheet_width = sheet.get_Parameter(DB.BuiltInParameter.SHEET_WIDTH).AsDouble()
#     sheet_height = sheet.get_Parameter(DB.BuiltInParameter.SHEET_Height).AsDouble()
#     max_height = 0
    
#     for view in views:
#         view_width, view_height = view.Outline.Max - view.Outline.Min
        
#         # check if view fits on current sheet, otherwise create new sheet
#         if x + view_width > sheet_width:
#             x = start_point[0]
#             y += max_height + spacing
#             max_height = 0
#             if y + view_height > sheet_height:
#                 raise ValueError("Views do not fit on sheet")
        
#         # add view to sheet
#         location_point = DB.XYZ(x, y, 0)
#         view_scale = (sheet_height / view_height) * 96
#         sheet.AddView(view, location_point, view_scale)
        
#         x += view_width + spacing
#         max_height = max(max_height, view_height)
        
def pack_views_on_sheet(views, sheet, border=(.25, 2.25, .25, .25)):
    top, right, bottom, left = (x/12 for x in border)
    sheet_width = sheet.Outline.Max.U - sheet.Outline.Min.U
    sheet_height = sheet.Outline.Max.V - sheet.Outline.Min.V
    usable_width = sheet_width - right - left
    usable_height = sheet_height - top - bottom
    
    x = left
    y = bottom
    # max_row_height = 0
    viewports = []
    title_offset = .85/12
    max_height = max(view.Outline.Max.V - view.Outline.Min.V + title_offset for view in views)
    
    with revit.Transaction("Pack Views"):
        for view in views:
            view_width = view.Outline.Max.U - view.Outline.Min.U
            view_height = view.Outline.Max.V - view.Outline.Min.V
            
            if x + view_width > usable_width:
                # print("too wide")
                x = left
                y += max_height
            
            if y + view_height > usable_height:
                raise ValueError("Not all views can fit in the sheet")
            
            vp = DB.Viewport.Create(
                revit.doc, 
                sheet.Id, 
                view.Id, 
                DB.XYZ(x + view_width/2 + title_offset, y + view_height/2 + title_offset, 0)
            )
            x += view_width
            viewports.append(vp)
        return viewports

