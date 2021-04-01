"""
This script creates sheets based on the number of views for each room. This is designed for the 11x17 Titleblock.
"""

#pylint: disable=import-error,invalid-name,broad-except
import clr
# Import RevitAPI
clr.AddReference("RevitAPI")
import Autodesk
import math
import itertools

from itertools import groupby, cycle
from Autodesk.Revit.DB import *

from pyrevit import revit
from pyrevit import script
from pyrevit import forms	

__title__ = " Create Sheets and Place Views by Room"
__author__ = "{{author}}"

top_left = XYZ(0.125, 0.65, 0)
bottom_left = XYZ(0.125, 0.25, 0)
top_right = XYZ(0.7, 0.65, 0)
bottom_right = XYZ(0.7, 0.25, 0)

# locs = [top_left, top_right, bottom_left, bottom_right]

# locs_cycle = cycle(locs)

# def next_loc():
#     return next(locs_cycle)

logger = script.get_logger()


selected_titleblocks = forms.select_titleblocks()
if selected_titleblocks:
    area_param_id = ElementId(BuiltInParameter.ROOM_AREA)
    area_param_prov = ParameterValueProvider(area_param_id)
    param_greater = FilterNumericGreater()
    filt = ElementParameterFilter(FilterDoubleRule(area_param_prov, param_greater, 0, 1E-6))
    # rooms = []
    rooms = FilteredElementCollector(revit.doc).WherePasses(filt).ToElements()
    # for c in col1:
    #     if c.Area != 0:
    #         rooms.append(c)

    views = []
    keys = []
    groups = []

    col2 = FilteredElementCollector(revit.doc).OfCategory(BuiltInCategory.OST_Views).ToElements()
    for view in col2:
        if not view.IsTemplate and view.LookupParameter("View Organization").AsString() == "FINAL DRAWINGS":
        # if not view.IsTemplate:
            views.append(view)
            # vName = view.ViewName.split("-")[1].strip()
            # data.append(vName)
    sort_order = ['FloorPlan', 'ThreeD', 'Elevation']
    
    sorted_views = []
    for x in sort_order:
        for view in views:
            if str(view.ViewType) == x:
                sorted_views.append(view)
    
    keyfunc = lambda x: x.ViewName.split("-")[1].strip()
    sorted_views.sort(key=keyfunc)
    for k, g in groupby(sorted_views, keyfunc):
        keys.append(k)
        groups.append(list(g))

    new_groups = []
    for group in groups:
        view_num = len(group)
        sheet_num = math.ceil(view_num/4.0)
                
        if view_num > 4:
            new_groups.append(group[:4])
            new_groups.append(group[4:])
        else:
            new_groups.append(group)



    currentSheets = []
    col3 = FilteredElementCollector(revit.doc).OfCategory(BuiltInCategory.OST_Sheets).ToElements()
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


with revit.Transaction("Create Sheets per Room"):
    sheet_list = []
    for idx, (room, group) in enumerate(zip(sorted(rooms), groups)):
        roomName = room.LookupParameter("Name").AsString().upper()
        roomNumber = room.LookupParameter("Number").AsString()
        startNumber = max_num + 1 + idx
        view_num = len(group)
        sheet_num = int(math.ceil(view_num/4.0))
        

        
        for i in range(0, sheet_num):
            newsheet = ViewSheet.Create(revit.doc, selected_titleblocks)
            newsheet.SheetNumber = str(startNumber + float(i)/10)
            newsheet.Name = roomName + " - " + roomNumber
            print('Creating sheet "%s: %s"' % (newsheet.SheetNumber, newsheet.Name))
            sheet_list.append(newsheet)

 
with revit.Transaction("Add Views to Sheets"):
               
    for s, gp in zip(sheet_list, new_groups):
        locs = [top_left, top_right, bottom_left, bottom_right]
        locs_cycle = cycle(locs)
        for g in gp:
            l = next(locs_cycle)
            # print(l)
            vp = Viewport.Create(revit.doc, s.Id, g.Id, l)
            print('\tAdding "%s" to sheet "%s"' % (g.ViewName, s.Name))

    # for g in new_groups:
    #     print(g)
            
        
print("Completed\n")
