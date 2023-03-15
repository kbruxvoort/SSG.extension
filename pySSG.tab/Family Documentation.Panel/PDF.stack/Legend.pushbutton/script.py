import math
import itertools
import rpw

from itertools import groupby
from datetime import date

from pyrevit import revit, DB
from pyrevit import forms
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

from Autodesk.Revit import Exceptions


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


def getOutlines(v, border_length_inches):
    w = 0
    l = 0

    oLine = v.Outline
    minU = oLine.Min.U - (border_length_inches) / 2
    minV = oLine.Min.V - (border_length_inches) / 2

    maxU = oLine.Max.U + (border_length_inches) / 2
    maxV = oLine.Max.V + (border_length_inches) / 2

    # get width and length of Rectangle
    w = maxU - minU
    l = maxV - minV

    return w, l


# Get list of multicategory tags to choose from
multi_tags = (
    DB.FilteredElementCollector(revit.doc)
    .OfCategory(DB.BuiltInCategory.OST_MultiCategoryTags)
    .WhereElementIsElementType()
    .ToElements()
)

# Get list of titleblocks to choose from
title_blocks = (
    DB.FilteredElementCollector(revit.doc)
    .OfCategory(DB.BuiltInCategory.OST_TitleBlocks)
    .WhereElementIsElementType()
)

# Get list of view templates to choose from
view_templates = []
all_views = DB.FilteredElementCollector(revit.doc).OfClass(DB.View).ToElements()
for view in all_views:
    if view.IsTemplate:
        view_templates.append(view)

# Get list of linestyles to choose from
cat = revit.doc.Settings.Categories.get_Item(DB.BuiltInCategory.OST_Lines)
gs = cat.GetGraphicsStyle(DB.GraphicsStyleType.Projection)
gsCat = gs.GraphicsStyleCategory.SubCategories

all_text = DB.FilteredElementCollector(revit.doc)
all_text.OfClass(DB.TextNoteType).ToElements()


components = [
    Label("Border Size"),
    ComboBox(
        "combobox1",
        {'1/8"': 0.125 / 12, '1/4"': 0.25 / 12, '1/2"': 0.5 / 12, '3/4"': 0.75 / 12},
        default='1/2"',
    ),
    Label("Tag Type"),
    ComboBox(
        "combobox2",
        list_to_dict_2(multi_tags),
        default="SSG_Tag_Multicategory: SSG_Prefix",
    ),
    Label("Titleblock"),
    ComboBox(
        "combobox3", list_to_dict_2(title_blocks), default="SSG_TB_8.5x11_PDF: Empty"
    ),
    Label("View Template"),
    ComboBox(
        "combobox4", list_to_dict(view_templates), default="SSG_Elevation - Legend"
    ),
    Label("Separator Line Style"),
    ComboBox(
        "combobox6",
        list_to_dict(all_text),
        default='SSG_3/32" - Segoe UI Semibold - Dark Blue',
    ),
    Label("Sheet Header"),
    ComboBox("combobox5", list_to_dict(gsCat), default="06"),
    Label("Header Text Style"),
    TextBox("textbox1", Text="Legend"),
    Button("Continue"),
]

form = FlexForm("Legend PDF", components)

if form.show():
    border_size = form.values["combobox1"]
    tag = form.values["combobox2"]
    pdf_tb = form.values["combobox3"]
    view_temp = form.values["combobox4"]
    text = form.values["combobox6"]
    line_style = form.values["combobox5"]
    short_descript = form.values["textbox1"]

    plan_view = revit.doc.ActiveView
    forms.check_viewtype(plan_view, DB.ViewType.FloorPlan, exitscript=True)
    today = date.today()
    today = today.strftime("%m/%d/%Y")

    with forms.WarningBar(title="Pick instances to add to legend:"):
        source_elements = revit.pick_elements()

    values = []
    if source_elements:

        # Filtering for current sheets to get highest sheet number
        current_sheets = []
        all_sheets = (
            DB.FilteredElementCollector(revit.doc)
            .OfCategory(DB.BuiltInCategory.OST_Sheets)
            .ToElements()
        )
        for s in all_sheets:
            try:
                num = math.floor(float(s.SheetNumber))
                current_sheets.append(num)
            except ValueError:
                continue
        # print("current sheets: ", current_sheets)
        if current_sheets:
            max_num = max(current_sheets)
        else:
            max_num = 0

        # Get the correct line style for the family separatation line
        sep_line = line_style.GetGraphicsStyle(DB.GraphicsStyleType.Projection)

        # Get default text
        default_text_id = revit.doc.GetDefaultElementTypeId(
            DB.ElementTypeGroup.TextNoteType
        )

        # Get Interior Elevation View Type
        v_types = []
        view_types = (
            DB.FilteredElementCollector(revit.doc)
            .OfClass(DB.ViewFamilyType)
            .ToElements()
        )
        for v in view_types:
            if "Interior Elevation" in DB.Element.Name.__get__(v):
                v_types.append(v)
        viewType = v_types[0]

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
        key_func = lambda x: x.Symbol.FamilyName
        source_elements = sorted(source_elements, key=key_func)

        fam_groups = []
        for k, g in groupby(source_elements, key=key_func):
            fam_groups.append(list(g))

        with revit.Transaction("Create Legend Elevations"):
            views = []
            order = []
            descrips = []
            for group in fam_groups:
                count = 1
                group_count = len(group)
                for ele in group:
                    loc = ele.Location.Point

                    # Get element Bounding Box and Create New
                    elementBB = ele.get_BoundingBox(plan_view)
                    gMax = elementBB.Max
                    gMin = elementBB.Min
                    width = gMax.X - gMin.X
                    depth = gMax.Y - gMin.Y
                    height = gMax.Z

                    offset = 3 + depth
                    marker_loc = loc.Add(DB.XYZ(0, -offset, 0))

                    # Create Elevation and assign legend view template
                    eleMarker = DB.ElevationMarker.CreateElevationMarker(
                        revit.doc, viewType.Id, marker_loc, 100
                    )
                    ele1 = eleMarker.CreateElevation(
                        revit.doc, revit.doc.ActiveView.Id, 1
                    )
                    ele1.ViewTemplateId = view_temp.Id
                    try:
                        ele1.Name = ele.Symbol.FamilyName + "-" + str(count)
                    except Exceptions.ArgumentException:
                        log.warning(
                            "Failed to rename. "
                            + ele.Symbol.FamilyName
                            + "-"
                            + str(count)
                            + "already exists."
                        )
                    revit.doc.Regenerate()

                    # Adjust cropbox to fit around just the element
                    crop_offset = 0.083
                    viewBB = ele1.get_BoundingBox(None)
                    viewBB.Min = DB.XYZ(
                        marker_loc.X - width / 2 - crop_offset,
                        marker_loc.Z - crop_offset,
                        0,
                    )
                    viewBB.Max = DB.XYZ(
                        marker_loc.X + width / 2 + crop_offset,
                        marker_loc.Z + height + crop_offset,
                        0,
                    )

                    ele1.CropBox = viewBB
                    ele1.CropBoxVisible = False
                    revit.doc.Regenerate()

                    farClip = ele1.get_Parameter(
                        DB.BuiltInParameter.VIEWER_BOUND_OFFSET_FAR
                    )
                    farClip.SetValueString(
                        str(depth + (offset - depth) + crop_offset) + "'"
                    )

                    # Tag View
                    tag_mode = DB.TagMode.TM_ADDBY_MULTICATEGORY
                    tag_orient = DB.TagOrientation.Horizontal
                    tag_name = "SSG_Tag_Multicategory"
                    tag_pt = loc.Add(DB.XYZ(0, 0, -0.5))

                    eleTag = revit.doc.Create.NewTag(
                        ele1, ele, False, tag_mode, tag_orient, tag_pt
                    )
                    eleTag.ChangeTypeId(tag.Id)
                    revit.doc.Regenerate()

                    if count == 1 and count == group_count:
                        order.append("Only")
                    elif count == 1:
                        order.append("First")
                    elif count == group_count:
                        order.append("Last")
                    else:
                        order.append("Middle")
                    count += 1

                    p = ele.Symbol.LookupParameter("SSG_Short Description").AsString()
                    descrips.append(p)
                    views.append(ele1)

        with revit.Transaction("Place views on legend sheet"):

            sheet_width = 0.625
            sheet_length = 8.5 / 12

            # print(border_size)
            widths, lengths = [], []
            for v in views:
                w, l = getOutlines(v, border_size)
                widths.append(w)
                lengths.append(l)
            max_width, max_length = max(widths), max(lengths)

            column_qty = int(sheet_width / max_width)
            row_qty = int(sheet_length / max_length)

            tile_width = sheet_width / column_qty
            tile_length = sheet_length / row_qty

            first_tile_loc = DB.XYZ(0.825 / 12, 9.5 / 12, 0)
            first_tile_pt = first_tile_loc.Add(
                DB.XYZ(tile_width / 2, -(tile_length / 2), 0)
            )

            total_views = column_qty * row_qty
            total_sheets = math.ceil(len(views) / float(total_views))

            Alert(
                'Max tile is {}" wide by {}" tall\nIt can be placed {} times in {} columns and {} rows\n{} sheets will be needed to fit {} views'.format(
                    tile_width * 12,
                    tile_length * 12,
                    total_views,
                    column_qty,
                    row_qty,
                    int(total_sheets),
                    len(source_elements),
                ),
                title="Legend PDF",
                header="Legend Tiling",
            )

            view_groups = [
                views[i : i + int(total_views)]
                for i in range(0, len(views), int(total_views))
            ]
            order_groups = [
                order[i : i + int(total_views)]
                for i in range(0, len(order), int(total_views))
            ]
            descrip_groups = [
                descrips[i : i + int(total_views)]
                for i in range(0, len(descrips), int(total_views))
            ]

            sheet_count = 1
            for group, order, descrips in zip(
                view_groups, order_groups, descrip_groups
            ):
                sheet = DB.ViewSheet.Create(revit.doc, pdf_tb.Id)
                sheet.SheetNumber = str(max_num + sheet_count)
                sheet.Name = "Legend"
                p1 = sheet.LookupParameter("SSG_Spec Short Description_1")
                p2 = sheet.LookupParameter("Sheet Issue Date")
                p1.Set(short_descript)
                p2.Set(today)

                size = len(group)
                if size < column_qty:
                    cols = size
                else:
                    cols = column_qty
                rows = math.ceil(size / column_qty)

                col = 1
                row = 1
                x = 0

                for v, o, d in zip(group, order, descrips):
                    if col > column_qty:
                        row += 1
                        col = 1
                        x = 0
                    y = (row - 1) * -tile_length

                    if o == "First" or o == "Only":
                        note = DB.TextNote.Create(
                            revit.doc,
                            sheet.Id,
                            first_tile_pt.Add(DB.XYZ(x, y, 0)).Add(
                                DB.XYZ(
                                    -tile_width / 2 + 0.125 / 12,
                                    tile_length / 2 + 0.125 / 12,
                                    0,
                                )
                            ),
                            "Short Name",
                            text.Id,
                        )
                    if o == "Last" or o == "Only":
                        l1 = DB.Line.CreateBound(
                            first_tile_pt.Add(
                                DB.XYZ(
                                    x + tile_width / 2,
                                    y - tile_length / 2 + 0.5 / 12,
                                    0,
                                )
                            ),
                            first_tile_pt.Add(
                                DB.XYZ(
                                    x + tile_width / 2,
                                    y + tile_length / 2 - 0.25 / 12,
                                    0,
                                )
                            ),
                        )
                        line_test = revit.doc.Create.NewDetailCurve(sheet, l1)
                        line_test.LineStyle = sep_line

                    vp = DB.Viewport.Create(
                        revit.doc, sheet.Id, v.Id, first_tile_pt.Add(DB.XYZ(x, y, 0))
                    )
                    vp.ChangeTypeId(vps[0].Id)

                    x += tile_width
                    col += 1
                    count += 1
                sheet_count += 1