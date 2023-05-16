from pyrevit import DB, forms



class ViewSizeError(Exception):
    pass

class Rectangle:
    def __init__(self, view, width, height, x=0, y=0):
        self.view = view
        self.width = width
        self.height = height
        self.x = x
        self.y = y


class Bin:
    def __init__(self, sheet, border_top=0, border_right=0, border_bottom=0, border_left=0):
        self.sheet = sheet
        self.border_top = border_top
        self.border_right = border_right
        self.border_bottom = border_bottom
        self.border_left = border_left
        self.x = border_left
        self.y = border_bottom
        self.width = self.sheet.Outline.Max.U - self.sheet.Outline.Min.U - self.border_left - self.border_right
        self.height = self.sheet.Outline.Max.V - self.sheet.Outline.Min.V - self.border_top - self.border_bottom
        self.remaining_areas = [Rectangle(None, self.width, self.height, self.border_left, self.border_bottom)]


def find_best_fit(bin, rectangle):
    best_fit_index = -1
    best_fit_area = float('inf')

    for i, remaining_area in enumerate(bin.remaining_areas):
        if remaining_area.width >= rectangle.width and remaining_area.height >= rectangle.height:
            remaining_area = remaining_area.width * remaining_area.height
            if remaining_area < best_fit_area:
                best_fit_area = remaining_area
                best_fit_index = i

    return best_fit_index


def split_rectangle(doc, sheet, rectangle, width, height, draw_cut_lines=False):
    remaining_areas = []
    if width < rectangle.width:
        remaining_areas.append(Rectangle(None, rectangle.width - width, rectangle.height, rectangle.x + width, rectangle.y))
        if draw_cut_lines:
            draw_cut_line(doc, sheet, rectangle.x + width, rectangle.y, rectangle.x + width, rectangle.y + rectangle.height)
    if height < rectangle.height:
        remaining_areas.append(Rectangle(None, width, rectangle.height - height, rectangle.x, rectangle.y + height))
        if draw_cut_lines:
            draw_cut_line(doc, sheet, rectangle.x, rectangle.y + height, rectangle.x + rectangle.width, rectangle.y + height)
    return remaining_areas

def place_view(doc, sheet_id, view_rectangle, point):
    if view_rectangle.view.ViewType == DB.ViewType.Schedule:
        return DB.ScheduleSheetInstance.Create(doc, sheet_id, view_rectangle.view.Id, point)
    else:
        return DB.Viewport.Create(doc, sheet_id, view_rectangle.view.Id, point)


def pack_views(doc, view_rectangles, titleblock, sheet_name=None, border_top=0, border_right=0, border_bottom=0, border_left=0, draw_cut_lines=False):
    sheet = DB.ViewSheet.Create(doc, titleblock)
    if sheet_name:
        sheet.Name = sheet_name
    start_bin = Bin(sheet, border_top, border_right, border_bottom, border_left)
    sheets = [start_bin]
    
    for view_rect in view_rectangles:
        if not is_view_valid(view_rect, start_bin.width, start_bin.height):
            forms.alert("{} is larger than the sheet".format(view_rect.view.Name), exitscript=True)
            # raise ViewSizeError("View {} is too large to fit on sheet".format(view_rect.view.Name))
        placed = False
        
        for sheet in sheets:
            best_fit_index = find_best_fit(sheet, view_rect)
            if best_fit_index != -1:
                remaining_area = sheet.remaining_areas.pop(best_fit_index)
                sheet.remaining_areas.extend(split_rectangle(doc, sheet.sheet, remaining_area, view_rect.width, view_rect.height, draw_cut_lines=draw_cut_lines))
                view_rect.x = remaining_area.x + view_rect.width / 2
                view_rect.y = remaining_area.y + view_rect.height / 2
                x_offset = sheet.border_left
                y_offset = sheet.border_bottom
                placement_pt = DB.XYZ(view_rect.x + x_offset, view_rect.y + y_offset, 0)
                placed_view = place_view(doc, sheet.sheet.Id, view_rect, placement_pt)
                placed = True
                break
            
        if not placed:
            new_sheet = DB.ViewSheet.Create(doc, titleblock)
            if sheet_name:
                new_sheet.Name = sheet_name
            new_sheet_bin = Bin(new_sheet, border_top, border_right, border_bottom, border_left)
            remaining_area = new_sheet_bin.remaining_areas.pop(0)
            new_sheet_bin.remaining_areas = split_rectangle(doc, new_sheet_bin.sheet, remaining_area, view_rect.width, view_rect.height, draw_cut_lines=draw_cut_lines)
            view_rect.x = remaining_area.x + view_rect.width / 2
            view_rect.y = remaining_area.y + view_rect.height / 2
            x_offset = sheet.border_left
            y_offset = sheet.border_bottom
            placement_pt = DB.XYZ(view_rect.x + x_offset, view_rect.y + y_offset, 0)
            placed_view = place_view(doc, new_sheet_bin.sheet.Id, view_rect, placement_pt)
            # DB.Viewport.Create(doc, new_sheet_bin.sheet.Id, view_rect.view.Id, placement_pt)
            sheets.append(new_sheet_bin)
            
    return sheets


def draw_cut_line(doc, sheet, x1, y1, x2, y2):
    # Create detail line to represent the guillotine cut
    line = DB.Line.CreateBound(DB.XYZ(x1, y1, 0), DB.XYZ(x2, y2, 0))

    # Create the detail line on the sheet
    doc.Create.NewDetailCurve(sheet, line)



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
        # DB.ViewType.Schedule
    ]
    return not view.IsTemplate \
           and view.Id not in placed_views \
           and view.ViewType in acceptable_types
           
def is_view_valid(view_rect, sheet_width, sheet_height):
    if view_rect.width > sheet_width or view_rect.height > sheet_height:
        return False
    return True