import math
import itertools

from itertools import cycle
from datetime import date

from pyrevit import revit, DB, UI 
from pyrevit import script
from pyrevit import forms


param_dict = {
    "SSG_Short Description": "SSG_Spec Short Description_",
    "SSG_Long Description": "SSG_Spec Long Description_",
    "STD_Widths": "SSG_Spec STD Widths_",
    "STD_Depths": "SSG_Spec STD Depths_",
    "STD_Heights": "SSG_Spec STD Heights_",
    }


output = script.get_output()
logger = script.get_logger()

First_Loc = DB.XYZ(1.81640625/12, 8.625/12, 0)
Second_Loc = DB.XYZ(1.81640625/12, 6.375/12, 0)
Third_Loc = DB.XYZ(1.81640625/12, 4.125/12, 0)
Fourth_Loc = DB.XYZ(1.81640625/12, 1.875/12, 0)


threeD_view = revit.doc.ActiveView 
forms.check_viewtype(threeD_view, DB.ViewType.ThreeD, exitscript=True)
viewTypeId = threeD_view.GetTypeId()

 


with forms.WarningBar(title='Pick source object:'):
    source_elements = revit.pick_elements()

if source_elements:

    # Get the secondary titleblock
    title_blocks = DB.FilteredElementCollector(revit.doc).OfCategory(DB.BuiltInCategory.OST_TitleBlocks).WhereElementIsElementType()
    pdf_tb = [t for t in title_blocks if t.FamilyName + ": " + t.LookupParameter("Type Name").AsString() == "SSG_TB_8.5x11_PDF: Secondary"][0]

    # Filtering for viewport type that hides the title
    col = DB.FilteredElementCollector(revit.doc).OfClass(DB.ElementType).ToElements()
    for c in col:
        p = c.LookupParameter('Title')
        if not p is None:
            if DB.Element.Name.__get__(c) == 'No Title':
                newVp = c
    
    # List of 3D views to compare to when creating new views
    names_3d = []
    all_3d = DB.FilteredElementCollector(revit.doc).OfClass(DB.View3D).ToElements()
    for v in all_3d:
        names_3d.append(v.Name)

    # Get the view templates required
    secondary_template = []
    all_views = DB.FilteredElementCollector(revit.doc).OfClass(DB.View).ToElements()
    for view in all_views:
        if view.IsTemplate:
            if view.Name == "SSG_3D - PDF Secondary":
                secondary_template.append(view)


    # Filtering for current sheets to get highest sheet number            
    current_sheets, sheet_names = [], []
    all_sheets = DB.FilteredElementCollector(revit.doc).OfCategory(DB.BuiltInCategory.OST_Sheets).ToElements()
    for s in all_sheets:
        try:
            num = math.floor(float(s.SheetNumber))
            current_sheets.append(num)
        except ValueError:
            continue
        sheet_names.append(s.Name)
    if current_sheets:
        max_num = max(current_sheets)
    else:
        max_num = 0


    max_value = len(source_elements)
    count = 0
    
    with forms.ProgressBar(title='PDF Creation ({value} of {max_value})') as pb:
        # Iterate through selection, create view with section box
        with revit.Transaction("Create Spec PDF"):
            # Chop list into groups of four so we know the right amount of sheets
            ele_groups = [source_elements[i:i + 4] for i in range(0, len(source_elements), 4)]
            sheet_total = math.ceil(len(source_elements)/4)

            for idx, group in enumerate(ele_groups):
                # sheet = DB.ViewSheet.Create(revit.doc, selected_titleblocks)
                sheet = DB.ViewSheet.Create(revit.doc, pdf_tb.Id)
                sheet.SheetNumber = str(max_num+idx+1)
                sheet.Name = "SPEC_Secondary_" + str(idx+1)
                tb = DB.FilteredElementCollector(revit.doc, sheet.Id).OfCategory(DB.BuiltInCategory.OST_TitleBlocks).WhereElementIsNotElementType().FirstElement()
                p = tb.LookupParameter("QTY_Families")
                if p:
                    p.Set(len(group))
                print('Creating new sheet ' + sheet.Name)

                # Create a cycle for the image location
                locs = [First_Loc, Second_Loc, Third_Loc, Fourth_Loc]
                locs_cycle = cycle(locs)
                param_count = 0
                for ele in group:
                    param_count += 1
                    type_id = ele.GetTypeId()
                    ele_type = revit.doc.GetElement(type_id)
                    ele_name = ele_type.FamilyName
                    print('Adding "{}" to PDF'.format(ele_name))

                    # Check to see if view already exists
                    if ele_name in names_3d:
                        view_3d = [v for v in all_3d if v.Name == ele_name][0]
                        print("\t3D view already exists. Placing view on new sheet")
                        
                    else:
                        # Get element Bounding Box and Create New
                        elementBB = ele.get_BoundingBox(threeD_view)
                        gMax = elementBB.Max
                        gMin = elementBB.Min
                        newMaxP = DB.XYZ(gMax.X + .1, gMax.Y + .1, gMax.Z + .1)
                        newMinP = DB.XYZ(gMin.X - .1, gMin.Y - .1, gMin.Z - .1)
                        newBB = DB.BoundingBoxXYZ()
                        newBB.Max = newMaxP
                        newBB.Min = newMinP
                        # Create New 3D View
                        view_3d = DB.View3D.CreateIsometric(revit.doc, viewTypeId)
                        DB.View3D.SetSectionBox(view_3d, newBB)
                        view_3d.Name = ele_name
                        revit.doc.Regenerate()
                        print('\tCreating 3D view and placing on new sheet')
                    
                    l = next(locs_cycle)
                    view_3d.ViewTemplateId = secondary_template[0].Id
                    revit.doc.Regenerate()
                    vp = DB.Viewport.Create(revit.doc, sheet.Id, view_3d.Id, l)
                    vp.ChangeTypeId(newVp.Id)

                    # Map parameters from family to specific sheet parameters
                    for k, v in param_dict.items():
                        p = sheet.LookupParameter(v + str(param_count))
                        value = ele.LookupParameter(k)
                        if not value:
                            value = ele_type.LookupParameter(k)
                        if p and value:
                            p.Set(value.AsString())
                    print('\tMapping Parameters to Sheet')
                    count += 1
                    pb.update_progress(count, max_value)
                
                # Set script run time as last edited date
                today = date.today()
                today = today.strftime("%m/%d/%Y")
                issue_date = sheet.get_Parameter(DB.BuiltInParameter.SHEET_ISSUE_DATE)
                issue_date.Set(today)
                    
