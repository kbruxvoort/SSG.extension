from pyrevit import DB


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

def split_rectangle(rectangle, width, height):
    remaining_areas = []
    if width < rectangle.width:
        remaining_areas.append(Rectangle(None, rectangle.width - width, rectangle.height, rectangle.x + width, rectangle.y))
    if height < rectangle.height:
        remaining_areas.append(Rectangle(None, width, rectangle.height - height, rectangle.x, rectangle.y + height))
    return remaining_areas


def pack_views(doc, view_rectangles, titleblock, border_top=0, border_right=0, border_bottom=0, border_left=0):
    sheet = DB.ViewSheet.Create(doc, titleblock)
    start_bin = Bin(sheet, border_top, border_right, border_bottom, border_left)
    sheets = [start_bin]
    
    for view_rect in view_rectangles:
        placed = False
        
        for sheet in sheets:
            best_fit_index = find_best_fit(sheet, view_rect)
            if best_fit_index != -1:
                remaining_area = sheet.remaining_areas.pop(best_fit_index)
                sheet.remaining_areas.extend(split_rectangle(remaining_area, view_rect.width, view_rect.height))
                view_rect.x = remaining_area.x + view_rect.width / 2
                view_rect.y = remaining_area.y + view_rect.height / 2
                x_offset = sheet.border_left
                y_offset = sheet.border_bottom
                placement_pt = DB.XYZ(view_rect.x + x_offset, view_rect.y + y_offset, 0)
                # print(view_rect.view.Name)
                # print(view_rect.width, view_rect.height)
                # print(placement_pt)
                # print("---------")
                DB.Viewport.Create(doc, sheet.sheet.Id, view_rect.view.Id, placement_pt)
                placed = True
                break
            
        if not placed:
            new_sheet = DB.ViewSheet.Create(doc, titleblock)
            new_sheet_bin = Bin(new_sheet, border_top, border_right, border_bottom, border_left)
            remaining_area = new_sheet_bin.remaining_areas.pop(0)
            new_sheet_bin.remaining_areas = split_rectangle(remaining_area, view_rect.width, view_rect.height)
            view_rect.x = remaining_area.x + view_rect.width / 2
            view_rect.y = remaining_area.y + view_rect.height / 2
            x_offset = sheet.border_left
            y_offset = sheet.border_bottom
            DB.Viewport.Create(doc, new_sheet_bin.sheet.Id, view_rect.view.Id, DB.XYZ(view_rect.x + x_offset, view_rect.y + y_offset, 0))
            sheets.append(new_sheet_bin)
            
    return sheets
