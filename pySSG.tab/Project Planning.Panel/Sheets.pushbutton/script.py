import math

from pyrevit import revit, script, forms, DB
from packing import sort_views, pack_views_on_sheet


# border_other = DB.UnitUtils.ConvertToInternalUnits(.25, DB.DisplayUnitType.DUT_DECIMAL_INCHES)
# border_right = DB.UnitUtils.ConvertToInternalUnits(2.25, DB.DisplayUnitType.DUT_DECIMAL_INCHES)
border_other = .25
border_right = .25
logger = script.get_logger()


selected_titleblock = forms.select_titleblocks()
if selected_titleblock:
    area_param_id = DB.ElementId(DB.BuiltInParameter.ROOM_AREA)
    area_param_prov = DB.ParameterValueProvider(area_param_id)
    param_greater = DB.FilterNumericGreater()
    filt = DB.ElementParameterFilter(
        DB.FilterDoubleRule(area_param_prov, param_greater, 0, 1e-6)
    )

    rooms = DB.FilteredElementCollector(revit.doc).WherePasses(filt).ToElements()
    sheets = DB.FilteredElementCollector(revit.doc).OfCategory(DB.BuiltInCategory.OST_Sheets)
    placed_views = []
    for sheet in sheets:
        placed_views.extend(sheet.GetAllPlacedViews())

    views = []
    keys = []
    groups = []

    views = (
        DB.FilteredElementCollector(revit.doc)
        .OfCategory(DB.BuiltInCategory.OST_Views)
        .ToElements()
    )
    grouped_views = {}
    
    for room in rooms:
        room_num = room.Number
        room_views = []
        room_sheets = []
        for view in views:
            if not view.IsTemplate and room_num in view.Name and view.Id not in placed_views:
                # and view.get_Parameter("View Organization").AsString() == "FINAL DRAWINGS"
                room_views.append(view)
        if room_views:    
            grouped_views[room_num] = {"unplaced_views": room_views}
        for sheet in sheets:
            if room_num in sheet.get_Parameter(DB.BuiltInParameter.SHEET_NAME).AsString():
                room_sheets.append(sheet)
        if room_sheets:
            grouped_views[room_num] = {"existing_sheets": room_sheets}
            # vName = view.Name.split("-")[1].strip()
            # data.append(vName)
    # sort_order = [
    #     "ThreeD",
    #     "Elevation"
    #     "FloorPlan", 
    #     "Section"
        
    # ]
    sort_order = [
        DB.ViewType.ThreeD,
        DB.ViewType.FloorPlan,
        DB.ViewType.Elevation, 
        DB.ViewType.Section, 

    ]
    for k,v in grouped_views.items():
        # view_widths = [view.Outline.Max.U - view.Outline.Min.U for view in v]
        # view_heights = [view.Outline.Max.V - view.Outline.Min.V for view in v]
        # print("Room {}".format(k))
        # print("\tWidths: {}".format(view_widths))
        # print("\tHeights: {}".format(view_heights))
        print(k, v)
    '''
    views = sort_views(views, sort_order)
    
    for v in views:
        view_type_index = sort_order.index(v.ViewType) if v.ViewType in sort_order else len(sort_order)
        width = v.Outline.Max.U - v.Outline.Min.U
        height = v.Outline.Max.V - v.Outline.Min.V
        area = width * height
        # print(v.Name, v.ViewType, area, view_type_index)
        
    sheet_id = 957271
    sheet = revit.doc.GetElement(DB.ElementId(sheet_id))
    # print(sheet)

    pack_views_on_sheet(views, sheet)
    # sorted_views = []
    # for x in sort_order:
    #     for view in views:
    #         if str(view.ViewType) == x:
    #             sorted_views.append(view)

    # keyfunc = lambda x: x.Name.split("-")[1].strip()
    # sorted_views.sort(key=keyfunc)
    # for k, g in groupby(sorted_views, keyfunc):
    #     keys.append(k)
    #     groups.append(list(g))

    # new_groups = []
    # for group in groups:
    #     view_num = len(group)
    #     sheet_num = math.ceil(view_num / 4.0)

    #     if view_num > 4:
    #         new_groups.append(group[:4])
    #         new_groups.append(group[4:])
    #     else:
    #         new_groups.append(group)
    '''
'''
    currentSheets = []
    col3 = (
        DB.FilteredElementCollector(revit.doc)
        .OfCategory(DB.BuiltInCategory.OST_Sheets)
        .ToElements()
    )
    for s in col3:
        try:
            num = float(s.SheetNumber)
            currentSheets.append(num)
        except ValueError:
            continue

    if currentSheets:
        max_num = math.floor(max(currentSheets))
    else:
        max_num = 0

    # for v in views:
    #     print(v.ViewType)

    with revit.Transaction("Create Sheets and Pack Views"):
        sheet_views = pack_views_on_sheets(
            views,
            revit.doc.GetElement(selected_titleblock),
            sheet_name="103",
            sheet_number=str(float(max_num+1)),
            view_type_order=sort_order,
            border=(border_other, border_right, border_other, border_other)
        )
#     sheet_list = []
#     for idx, (room, group) in enumerate(zip(sorted(rooms), groups)):
#         roomName = room.LookupParameter("Name").AsString()
#         roomNumber = room.LookupParameter("Number").AsString()
#         startNumber = max_num + 1 + idx
#         view_num = len(group)
#         sheet_num = int(math.ceil(view_num / 4.0))

#         for i in range(0, sheet_num):
#             newsheet = ViewSheet.Create(revit.doc, selected_titleblocks)
#             newsheet.SheetNumber = str(startNumber + float(i) / 10)
#             newsheet.Name = roomName + " - " + roomNumber
#             print('Creating sheet "%s: %s"' % (newsheet.SheetNumber, newsheet.Name))
#             sheet_list.append(newsheet)


# with revit.Transaction("Add Views to Sheets"):

#     for s, gp in zip(sheet_list, new_groups):
#         locs = [top_left, top_right, bottom_left, bottom_right]
#         locs_cycle = cycle(locs)
#         for g in gp:
#             l = next(locs_cycle)
#             # print(l)
#             vp = Viewport.Create(revit.doc, s.Id, g.Id, l)
#             print('\tAdding "%s" to sheet "%s"' % (g.Name, s.Name))

#     # for g in new_groups:
#     #     print(g)


# print("Completed\n")
'''