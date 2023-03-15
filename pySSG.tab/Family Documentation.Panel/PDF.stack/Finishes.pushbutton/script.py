# from doc_utils import max_sheet_num, get_rectangle, is_float
import math
import itertools
import rpw

from ssgutils import max_sheet_num, get_rectangle
from itertools import groupby
from datetime import date


# from pyrevit.coreutils import Timer
# timer = Timer()
from Autodesk.Revit import Exceptions
from pyrevit import revit, DB, forms, HOST_APP
from rpw.ui.forms import (
    FlexForm,
    Label,
    ComboBox,
    TextBox,
    TextBox,
    Separator,
    Button,
    CheckBox,
    Alert,
)


def list_to_dict(e_list, attr="Name"):
    ele_list, properties = [], []
    for l in e_list:
        ele_list.append(l)
        try:
            properties.append(getattr(l, attr))
        except:
            properties.append(DB.Element.Name.__get__(l))

    d1 = zip(properties, ele_list)
    return dict(d1)


def list_to_dict_2(e_list):
    ele_list, properties = [], []
    for l in e_list:
        ele_list.append(l)
        properties.append("{}: {}".format(l.FamilyName, DB.Element.Name.__get__(l)))

    d1 = zip(properties, ele_list)
    return dict(d1)


plan_view = revit.doc.ActiveView
# forms.check_viewtype(plan_view, DB.ViewType.FloorPlan, exitscript=True)
today = date.today()
today = today.strftime("%m/%d/%Y")


# Get list of multicategory tags to choose from
mat_tags = DB.FilteredElementCollector(revit.doc)
mat_tags.OfCategory(DB.BuiltInCategory.OST_MaterialTags)
mat_tags.WhereElementIsElementType().ToElements()

# Get list of titleblocks to choose from
title_blocks = DB.FilteredElementCollector(revit.doc)
title_blocks.OfCategory(DB.BuiltInCategory.OST_TitleBlocks).WhereElementIsElementType()

# Get list of view templates to choose from
view_templates = []
all_views = DB.FilteredElementCollector(revit.doc).OfClass(DB.View).ToElements()
for view in all_views:
    if view.IsTemplate:
        view_templates.append(view)

all_text = DB.FilteredElementCollector(revit.doc)
all_text.OfClass(DB.TextNoteType).ToElements()

# endtime = timer.get_time()
# print(endtime)


components = [
    Label("Border Size"),
    ComboBox(
        "combobox1",
        {'1/8"': 0.125 / 12, '1/4"': 0.25 / 12, '1/16"': 0.0625 / 12, "None": 0.001},
        default='1/16"',
    ),
    Label("Tag Type"),
    ComboBox(
        "combobox2",
        list_to_dict_2(mat_tags),
        default="SSG_Tag_Material_Swatch: Default",
    ),
    Label("Titleblock"),
    ComboBox(
        "combobox3", list_to_dict_2(title_blocks), default="SSG_TB_8.5x11_PDF: Empty"
    ),
    Label("View Template"),
    ComboBox("combobox4", list_to_dict(view_templates), default="SSG_Plan - Swatch"),
    Label("Header Text Style"),
    ComboBox(
        "combobox5",
        list_to_dict(all_text),
        default='SSG_1/8" - Segoe UI Semibold - Dark Blue',
    ),
    Label("Sheet Header"),
    TextBox("textbox1", Text="Finish Options"),
    Button("Continue"),
]

form = FlexForm("Finish Options PDF", components)

if form.show():
    border_size = form.values["combobox1"]
    tag = form.values["combobox2"]
    pdf_tb = form.values["combobox3"]
    view_temp = form.values["combobox4"]
    text = form.values["combobox5"]
    short_descript = form.values["textbox1"]

    all_mats = DB.FilteredElementCollector(revit.doc).OfCategory(
        DB.BuiltInCategory.OST_Materials
    )

    ssg_mats = [m for m in all_mats if "SSG" in m.Name]

    res = forms.SelectFromList.show(
        ssg_mats, multiselect=True, name_attr="Name", button_name="Select Material"
    )

    if res:

        gen_fams = (
            DB.FilteredElementCollector(revit.doc)
            .OfCategory(DB.BuiltInCategory.OST_GenericModel)
            .OfClass(DB.FamilySymbol)
        )

        swatch_fam_type = [x for x in gen_fams if x.FamilyName == "SSG_Mat_Swatch"][0]
        # print(swatch_fam_type.FamilyName)

        # Filtering for current sheets to get highest sheet number

        # current_sheets = []
        all_sheets = (
            DB.FilteredElementCollector(revit.doc)
            .OfCategory(DB.BuiltInCategory.OST_Sheets)
            .ToElements()
        )
        max_num = max_sheet_num(all_sheets)
        # for s in all_sheets:
        #     try:
        #         num = math.floor(float(s.SheetNumber))
        #         current_sheets.append(num)
        #     except ValueError:
        #         continue

        # if current_sheets:
        #     max_num = max(current_sheets)
        # else:
        #     max_num = 0

        # Get default text
        default_text_id = revit.doc.GetDefaultElementTypeId(
            DB.ElementTypeGroup.TextNoteType
        )

        # Filtering for viewport type that hides the title
        vps = []
        ele_types = (
            DB.FilteredElementCollector(revit.doc).OfClass(DB.ElementType).ToElements()
        )
        for c in ele_types:
            p = c.LookupParameter("Title")
            if not p is None:
                if DB.Element.Name.__get__(c) == "No Title":
                    vps.append(c)

        # Sort Selection By Family
        key_func = lambda x: x.get_Parameter(
            DB.BuiltInParameter.ALL_MODEL_INSTANCE_COMMENTS
        ).AsString()
        res = sorted(res, key=key_func)

        mat_groups = []
        group_names = []
        for k, g in groupby(res, key=key_func):
            mat_groups.append(list(g))
            group_names.append(k)

        # Get active view level
        current_level = []
        levels = DB.FilteredElementCollector(revit.doc).OfClass(DB.Level).ToElements()
        for l in levels:
            if l.Name == plan_view.LookupParameter("Associated Level").AsString():
                current_level.append(l)
        levelId = current_level[0].Id

        key_func_2 = lambda x: x.get_Parameter(
            DB.BuiltInParameter.ALL_MODEL_DESCRIPTION
        ).AsString()
        with revit.Transaction("Create Material Swatches"):
            views = []
            group_nums = []
            x = 0
            if not swatch_fam_type.IsActive:
                swatch_fam_type.Activate()
                revit.doc.Regenerate()
            for group in mat_groups:
                count = 1
                group = sorted(group, key=key_func_2)
                for mat in group:
                    swatch = revit.doc.Create.NewFamilyInstance(
                        DB.XYZ(x, 0, 0),
                        swatch_fam_type,
                        DB.Structure.StructuralType.NonStructural,
                    )
                    x += 2
                    p = swatch.LookupParameter("MAT_Finish")
                    p.Set(mat.Id)
                    revit.doc.Regenerate()
                    loc = swatch.Location.Point
                    elementBB = swatch.get_BoundingBox(plan_view)

                    # Create plan view
                    viewTypeId = plan_view.GetTypeId()
                    plan1 = DB.ViewPlan.Create(revit.doc, viewTypeId, levelId)

                    # Set the new Bounding Box
                    plan1.CropBoxActive = True
                    plan1.CropBoxVisible = False

                    plan1.CropBox = elementBB
                    aCrop = plan1.get_Parameter(
                        DB.BuiltInParameter.VIEWER_ANNOTATION_CROP_ACTIVE
                    )
                    aCrop.Set(True)
                    plan1.ViewTemplateId = view_temp.Id
                    try:
                        plan1.Name = mat.Name
                        # plan1.Name = mat.Name
                    except Exceptions.ArgumentException:
                        print("Failed to name view " + mat.Name)

                    # Tag View
                    tag_mode = DB.TagMode.TM_ADDBY_MATERIAL
                    tag_orient = DB.TagOrientation.Horizontal
                    tag_pt = loc.Add(DB.XYZ(0, 0, 0))

                    if not tag.IsActive:
                        tag.Activate()
                        revit.doc.Regnerate()

                    # Material tags create method changed in 2019 API
                    app = revit.doc.Application
                    if int(app.VersionNumber) < 2019:
                        eleTag = revit.doc.Create.NewTag(
                            plan1, swatch, False, tag_mode, tag_orient, tag_pt
                        )
                        eleTag.ChangeTypeId(tag.Id)
                    else:
                        eleTag = DB.IndependentTag.Create(
                            revit.doc,
                            plan1.Id,
                            DB.Reference(swatch),
                            False,
                            tag_mode,
                            tag_orient,
                            tag_pt,
                        )
                        eleTag.ChangeTypeId(tag.Id)

                    views.append(plan1)

                    if count == len(group):
                        group_nums.append("Last")
                    elif count == 1:
                        group_nums.append("First")
                    else:
                        group_nums.append("other")

                    count += 1

        with revit.Transaction("Place views on finish sheet"):
            # TODO make this dims dynamic
            sheet_width = 0.625
            sheet_length = 8.5 / 12

            widths, lengths = [], []
            for v in views:
                w, l = get_rectangle(v)
                widths.append(w)
                lengths.append(l)
            max_width, max_length = max(widths), max(lengths)

            column_qty = int(sheet_width / max_width)
            row_qty = int(sheet_length / max_length)

            tile_width = sheet_width / column_qty
            tile_length = sheet_length / row_qty

            # TODO make start point dynamic
            first_tile_loc = DB.XYZ(0.825 / 12, 9.5 / 12, 0)
            first_tile_pt = first_tile_loc.Add(
                DB.XYZ(tile_width / 2, -(tile_length / 2), 0)
            )

            total_views = column_qty * row_qty
            total_sheets = math.ceil(len(views) / float(total_views))

            Alert(
                'Max tile is {}" wide by {}" tall\nIt can be placed {} times in {} columns and {} rows'.format(
                    tile_width * 12, tile_length * 12, total_views, column_qty, row_qty
                ),
                title="Finish Options PDF",
                header="Swatch Tiling",
            )

            col = 1
            row = 1
            sheet_count = 1
            view_count = total_views
            sheet = DB.ViewSheet.Create(revit.doc, pdf_tb.Id)
            sheet.SheetNumber = str(max_num + sheet_count)
            sheet.Name = "Finish Options"
            p1 = sheet.LookupParameter("SSG_Spec Short Description_1")
            p2 = sheet.LookupParameter("Sheet Issue Date")
            p1.Set(short_descript)
            p2.Set(today)

            i = 0
            x, y = 0, 0
            group_id = 0
            for v, n in zip(views, group_nums):
                if i == 0:
                    # create header
                    note = DB.TextNote.Create(
                        revit.doc,
                        sheet.Id,
                        first_tile_pt.Add(DB.XYZ(0, (row - 1) * -tile_length, 0)).Add(
                            DB.XYZ(-tile_width / 2, tile_length / 2 + 0.25 / 12, 0)
                        ),
                        group_names[group_id],
                        text.Id,
                    )
                elif view_count < 1:
                    col = 1
                    row = 1
                    sheet_count += 1
                    sheet = DB.ViewSheet.Create(revit.doc, pdf_tb.Id)
                    sheet.SheetNumber = str(max_num + sheet_count)
                    sheet.Name = "Finish Options"
                    p1 = sheet.LookupParameter("SSG_Spec Short Description_1")
                    p2 = sheet.LookupParameter("Sheet Issue Date")
                    p1.Set(short_descript)
                    p2.Set(today)
                    view_count = total_views
                elif n == "First":
                    row += 2
                    view_count -= column_qty + column_qty - col + 1
                    col = 1
                    group_id += 1
                    if view_count < 1:
                        row = 1
                        sheet_count += 1
                        sheet = DB.ViewSheet.Create(revit.doc, pdf_tb.Id)
                        sheet.SheetNumber = str(max_num + sheet_count)
                        sheet.Name = "Finish Options"
                        p1 = sheet.LookupParameter("SSG_Spec Short Description_1")
                        p2 = sheet.LookupParameter("Sheet Issue Date")
                        p1.Set(short_descript)
                        p2.Set(today)
                        view_count = total_views
                    # create header
                    note = DB.TextNote.Create(
                        revit.doc,
                        sheet.Id,
                        first_tile_pt.Add(DB.XYZ(0, (row - 1) * -tile_length, 0)).Add(
                            DB.XYZ(-tile_width / 2, tile_length / 2 + 0.25 / 12, 0)
                        ),
                        group_names[group_id],
                        text.Id,
                    )
                elif col > column_qty:
                    row += 1
                    col = 1

                x = (col - 1) * tile_width
                y = (row - 1) * -tile_length
                vp = DB.Viewport.Create(
                    revit.doc, sheet.Id, v.Id, first_tile_pt.Add(DB.XYZ(x, y, 0))
                )
                vp.ChangeTypeId(vps[0].Id)

                col += 1
                view_count -= 1
                i += 1
                revit.doc.Regenerate()
