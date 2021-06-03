import itertools
import math
import System.Collections.Generic.IEnumerable as IEnumerable
from itertools import groupby
from datetime import date

from pyrevit import revit, DB, UI
from pyrevit import script
from pyrevit import forms

# parameters to map from family to sheet
param_dict = {
    "SSG_Short Description": "SSG_Spec Short Description_1",
    "SSG_Long Description": "SSG_Spec Long Description_1",
    "STD_Widths": "SSG_Spec STD Widths_1",
    "STD_Depths": "SSG_Spec STD Depths_1",
    "STD_Heights": "SSG_Spec STD Heights_1",
    "SSG_Product Code": "SSG_Spec Current Config",
    "Keynote": "SSG_Spec Masterformat",
    "Assembly Code": "SSG_Spec Uniformat",
    "OmniClass Number": "SSG_Spec Omniclass",
}


output = script.get_output()
logger = script.get_logger()

# view locations for placement
top_left = DB.XYZ(2.56640625 / 12, 7.578125 / 12, 0)
mid_right = DB.XYZ(4.81640625 / 12, 8.08984375 / 12, 0)
sched_loc = DB.XYZ(0.81640625 / 12, 10.08984375 / 12, 0)

threeD_view = revit.doc.ActiveView
forms.check_viewtype(threeD_view, DB.ViewType.ThreeD, exitscript=True)
viewTypeId = threeD_view.GetTypeId()

today = date.today()
today = today.strftime("%m/%d/%Y")


with forms.WarningBar(title="Pick source object:"):
    source_elements = revit.pick_elements()

values = []
if source_elements:

    # Get all SSG Families
    mfg_param_id = DB.ElementId(DB.BuiltInParameter.ALL_MODEL_MANUFACTURER)
    mfg_param_prov = DB.ParameterValueProvider(mfg_param_id)
    param_contains = DB.FilterStringContains()
    mfg_value_rule = DB.FilterStringRule(
        mfg_param_prov, param_contains, "Southwest Solutions Group", False
    )
    param_filter = DB.ElementParameterFilter(mfg_value_rule)
    ssg_fams = (
        DB.FilteredElementCollector(revit.doc)
        .WherePasses(param_filter)
        .WhereElementIsNotElementType()
        .ToElements()
    )

    # Get the secondary titleblock
    title_blocks = (
        DB.FilteredElementCollector(revit.doc)
        .OfCategory(DB.BuiltInCategory.OST_TitleBlocks)
        .WhereElementIsElementType()
    )
    pdf_tb = [
        t
        for t in title_blocks
        if t.FamilyName + ": " + t.LookupParameter("Type Name").AsString()
        == "SSG_TB_8.5x11_PDF: Primary"
    ][0]
    pdf_tb_2 = [
        t
        for t in title_blocks
        if t.FamilyName + ": " + t.LookupParameter("Type Name").AsString()
        == "SSG_TB_8.5x11_PDF: Empty"
    ][0]

    # Filtering for viewport type that hides the title
    col = DB.FilteredElementCollector(revit.doc).OfClass(DB.ElementType).ToElements()
    for c in col:
        p = c.LookupParameter("Title")
        if not p is None:
            if DB.Element.Name.__get__(c) == "No Title":
                newVp = c

    # List of 3D views to compare to when creating new views
    names_3d = []
    all_3d = DB.FilteredElementCollector(revit.doc).OfClass(DB.View3D).ToElements()
    for v in all_3d:
        names_3d.append(v.ViewName)

    # Get the view templates required
    primary_template = []

    all_views = DB.FilteredElementCollector(revit.doc).OfClass(DB.View).ToElements()
    for view in all_views:
        if view.IsTemplate:
            if view.ViewName == "SSG_3D - PDF Primary":
                primary_template.append(view)

    # Filtering for current sheets to get highest sheet number
    current_sheets, sheet_names = [], []
    all_sheets = (
        DB.FilteredElementCollector(revit.doc)
        .OfCategory(DB.BuiltInCategory.OST_Sheets)
        .ToElements()
    )
    for s in all_sheets:
        sheet_names.append(s.Name)
        try:
            num = math.floor(float(s.SheetNumber))
            current_sheets.append(num)
        except ValueError:
            continue

    if current_sheets:
        max_num = max(current_sheets)
    else:
        max_num = 0

    # Filtering for Spec Schedule and getting current filter
    all_schedules = (
        DB.FilteredElementCollector(revit.doc).OfClass(DB.ViewSchedule).ToElements()
    )
    spec_schedules = []
    schedule_names = []
    for s in all_schedules:
        schedule_names.append(s.Name)
        if "SPEC" in s.ViewName:
            spec_schedules.append(s)

    ref_def = spec_schedules[0].Definition
    ref_filt = ref_def.GetFilter(0)
    field_ids = ref_def.GetFieldOrder()
    fields = []
    for field_id in field_ids:
        field = ref_def.GetField(field_id)
        if field.GetName() == "Comments":
            fields.append(field_id)

    # Set family as comments for schedule filter. If more than max_rows split into 2
    with revit.Transaction("Settings comments for filter"):
        key_func1 = lambda x: x.Symbol.Family.Name
        key_func2 = lambda x: x.LookupParameter("SSG_Product Code")
        ssg_fams = sorted(ssg_fams, key=key_func1)
        groups = []
        for k, g in groupby(ssg_fams, key=key_func1):
            # print(k + ": " + str(len(list(g))))
            groups.append(list(g))

        overflow = []
        max_rows = 38
        # groups = sorted(groups, key=key_func2)
        for fams in groups:
            if len(fams) > max_rows:
                fams = sorted(fams, key=key_func2)
                overflow.append(fams[0].Symbol.FamilyName)
                # print("Over " + str(max_rows))

                for f in fams[:max_rows]:
                    p = f.get_Parameter(DB.BuiltInParameter.ALL_MODEL_INSTANCE_COMMENTS)
                    type_id = f.GetTypeId()
                    fam_type = revit.doc.GetElement(type_id)
                    p.Set("SPEC_" + fam_type.FamilyName + "-1")

                for f in fams[max_rows:]:
                    p = f.get_Parameter(DB.BuiltInParameter.ALL_MODEL_INSTANCE_COMMENTS)
                    type_id = f.GetTypeId()
                    fam_type = revit.doc.GetElement(type_id)
                    p.Set("SPEC_" + fam_type.FamilyName + "-2")
            else:
                # print("Less than " + str(max_rows))
                for f in fams:
                    p = f.get_Parameter(DB.BuiltInParameter.ALL_MODEL_INSTANCE_COMMENTS)
                    type_id = f.GetTypeId()
                    fam_type = revit.doc.GetElement(type_id)
                    p.Set("SPEC_" + fam_type.FamilyName + "-1")

            # p = fam.get_Parameter(DB.BuiltInParameter.ALL_MODEL_INSTANCE_COMMENTS)
            # type_id = fam.GetTypeId()
            # fam_type = revit.doc.GetElement(type_id)
            # p.Set(fam_type.FamilyName)

    max_value = len(source_elements)
    count = 0

    with forms.ProgressBar(title="PDF Creation ({value} of {max_value})") as pb:
        # Iterate through selection, create view with section box
        for idx, source_element in enumerate(source_elements):
            with revit.Transaction("Create Spec PDF"):
                type_id = source_element.GetTypeId()
                ele_type = revit.doc.GetElement(type_id)
                ele_name = ele_type.FamilyName
                print("Creating SPEC for {}".format(ele_name))

                name_1 = "SPEC_" + ele_name + "-1"
                name_2 = "SPEC_" + ele_name + "-2"
                # If the family has more than max rows
                if ele_name in overflow:
                    # Check if second sheet already exists for this family
                    if name_2 in sheet_names:
                        sheet_2 = [s for s in all_sheets if s.Name == name_2][0]
                        print("\tSheet 2 already exists.")
                    else:
                        sheet_2 = DB.ViewSheet.Create(revit.doc, pdf_tb_2.Id)
                        sheet_2.SheetNumber = str(max_num + idx + 1.1)
                        sheet_2.Name = name_2
                        print("\tCreating new sheet 2")

                    # Check for schedules on sheet
                    sheet_scheds = (
                        DB.FilteredElementCollector(revit.doc, sheet_2.Id)
                        .OfClass(DB.ScheduleSheetInstance)
                        .ToElements()
                    )
                    # If there is no schedule on the sheet see if it already exists in the project
                    if not sheet_scheds:
                        if name_2 in schedule_names:
                            sched_2 = [s for s in all_schedules if s.Name == name_2][0]
                            print(
                                "\tSchedule 2 already exists. Placing schedule 2 on sheet 2"
                            )
                        else:
                            # Duplicate base schedule and set filter
                            new_sched_id = spec_schedules[0].Duplicate(
                                DB.ViewDuplicateOption.Duplicate
                            )
                            sched_2 = revit.doc.GetElement(new_sched_id)
                            sched_2.ViewName = name_2
                            tgt_filter = DB.ScheduleFilter(
                                fields[0], ref_filt.FilterType, name_2
                            )
                            new_sched_def = sched_2.Definition
                            new_sched_def.SetFilter(0, tgt_filter)
                            print("\tCreating Schedule 2 and placing on sheet 2")
                        # Place schedule on sheet
                        sched_inst_2 = DB.ScheduleSheetInstance.Create(
                            revit.doc, sheet_2.Id, sched_2.Id, sched_loc
                        )
                    else:
                        print("\tSchedule 2 is already placed on sheet 2")

                    p = sheet_2.LookupParameter("SSG_Spec Short Description_1")
                    value = source_element.LookupParameter("SSG_Short Description")
                    if not value:
                        value = ele_type.LookupParameter("SSG_Short Description")
                    p.Set(value.AsString())

                    issue_date = sheet_2.get_Parameter(
                        DB.BuiltInParameter.SHEET_ISSUE_DATE
                    )
                    issue_date.Set(today)
                    print("\tMapping Parameters to Sheet 2")

                # Check if first sheet already exists for this family
                if name_1 in sheet_names:
                    print("\tSheet 1 already exists.")
                    sheet_1 = [s for s in all_sheets if s.Name == name_1][0]
                else:
                    sheet_1 = DB.ViewSheet.Create(revit.doc, pdf_tb.Id)
                    sheet_1.SheetNumber = str(max_num + idx + 1)
                    sheet_1.Name = name_1
                    print("\tCreating new sheet 1")

                # Get all viewports on sheet
                viewports = sheet_1.GetAllViewports()

                # Check if the 3d exists but isn't on the sheet
                if not viewports:
                    if ele_name in names_3d:
                        view_3d = [v for v in all_3d if v.ViewName == ele_name][0]
                        print("\t3D view already exists. Placing view on sheet 1")
                    else:
                        # Create New 3D View w/ Section Box
                        elementBB = source_element.get_BoundingBox(threeD_view)
                        view_3d = DB.View3D.CreateIsometric(revit.doc, viewTypeId)
                        DB.View3D.SetSectionBox(view_3d, elementBB)
                        view_3d.Name = ele_name
                        print("\tCreating 3D view and placing on sheet 1")
                        revit.doc.Regenerate()

                    # Apply template to view and place on sheet
                    view_3d.ViewTemplateId = primary_template[0].Id
                    revit.doc.Regenerate()
                    vp = DB.Viewport.Create(revit.doc, sheet_1.Id, view_3d.Id, top_left)
                    vp.ChangeTypeId(newVp.Id)
                else:
                    print("\t3D is already placed on sheet 1")

                # Check for schedules on sheet
                sheet_scheds = (
                    DB.FilteredElementCollector(revit.doc, sheet_1.Id)
                    .OfClass(DB.ScheduleSheetInstance)
                    .ToElements()
                )
                # If there is no schedule on the sheet see if it already exists in the project
                if not sheet_scheds:
                    if name_1 in schedule_names:
                        sched_1 = [s for s in all_schedules if s.Name == name_1][0]
                        print(
                            "\tSchedule 1 already exists. Placing schedule 1 on sheet 1"
                        )
                    else:
                        # Duplicate base schedule and set filter
                        new_sched_id = spec_schedules[0].Duplicate(
                            DB.ViewDuplicateOption.Duplicate
                        )
                        sched_1 = revit.doc.GetElement(new_sched_id)
                        sched_1.ViewName = name_1
                        tgt_filter = DB.ScheduleFilter(
                            fields[0], ref_filt.FilterType, name_1
                        )
                        new_sched_def = sched_1.Definition
                        new_sched_def.SetFilter(0, tgt_filter)
                        print("\tCreating Schedule 1 and placing on sheet 1")
                    # Place schedule on sheet
                    sched_inst_1 = DB.ScheduleSheetInstance.Create(
                        revit.doc, sheet_1.Id, sched_1.Id, mid_right
                    )
                else:
                    print("\tSchedule 1 is already placed on sheet 1")

                    #######################################################
                for k, v in param_dict.items():
                    p = sheet_1.LookupParameter(v)
                    value = source_element.LookupParameter(k)
                    if not value:
                        value = ele_type.LookupParameter(k)
                    value = value.AsString()
                    p.Set(str(value))
                issue_date = sheet_1.get_Parameter(DB.BuiltInParameter.SHEET_ISSUE_DATE)
                issue_date.Set(today)
                print("\tMapping Parameters to Sheet 1")

                count += 1
                pb.update_progress(count, max_value)