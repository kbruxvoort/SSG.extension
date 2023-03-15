from pyrevit import revit, DB
from collect import get_placed_rooms
from schedules import ScheduleWrapper
from text_notes import TextType
from color import Color

with revit.Transaction("create font"):
    # print(Color("F15A24").get_rgb())
    orange = Color("F15A24")
    new_text = TextType.create(
        # name="New Text 2",
        italic=True,
        bold=True,
        is_transparent=False,
        color=Color("#F15A24").int_value,
        font="Comic Sans MS",
        size=3.0/16.0/12.0,
        underline=True
    )

'''
def duplicate_schedule(schedule, new_name=None):
    new_schedule_id = schedule.Duplicate(DB.ViewDuplicateOption.Duplicate)
    new_schedule = revit.doc.GetElement(new_schedule_id)
    if new_name:
        new_schedule.Name = new_name
    else:
        new_schedule.Name = schedule.Name + " Copy"
    return new_schedule
        


schedule_name = "SSG_Master Schedule"

rooms = get_placed_rooms(revit.doc)
schedules = revit.query.get_all_schedules(revit.doc)

# my_schedule = next(iter([s for s in schedules if s.Name == schedule_name]), None)
my_schedule = None

field_list = [
    {"field_name": "Room: Number", "hidden": True},
    {"field_name": "Manufacturer", "hidden": True},
    {"field_name": "Family and Type", "width": 3/12.0},
    {"field_name": "SSG_Product Code", "heading": "Product Code", "width": 2.0/12.0},
    {"field_name": "Count", "width": 0.5/12.0, "alignment": DB.ScheduleHorizontalAlignment.Right, "calculate_totals": True},
    {"field_name": "ACTUAL_Width", "heading": "Width", "width": 0.5/12.0, "alignment": DB.ScheduleHorizontalAlignment.Right},
    {"field_name": "ACTUAL_Depth", "heading": "Depth", "width": 0.5/12.0, "alignment": DB.ScheduleHorizontalAlignment.Right},
    {"field_name": "ACTUAL_Height", "heading": "Height", "width": 0.5/12.0, "alignment": DB.ScheduleHorizontalAlignment.Right},
    {"field_name": "TOTAL_List Price", "heading": "List Price", "width": 0.75/12.0, "alignment": DB.ScheduleHorizontalAlignment.Right, "calculate_totals": True}
    
]

if not my_schedule:
    # Create schedule
    with revit.Transaction("Create Schedule"):
        new_schedule = ScheduleWrapper.create(revit.doc, name="SSG Equipment Schedule", show_grand_total=True, show_grand_total_title=True, grand_total_title="The Whole Enchilada")
        # field_list = ["Room: Number", "Family and Type", "SSG_Product Code", "Count", "ACTUAL_Width", "ACTUAL_Depth", "ACTUAL_Height", "TOTAL_List Price"]
        for f in field_list:
            new_schedule.add_field(f.get("field_name"), heading=f.get("heading"), width=f.get("width"), alignment=f.get("alignment"), hidden=f.get("hidden", False), calculate_totals=f.get("calculate_totals", False))
        # new_schedule.add_fields(field_list)
        new_schedule.format_field("ACTUAL_Width", display_units=DB.DisplayUnitType.DUT_DECIMAL_INCHES, symbol=DB.UnitSymbolType.UST_INCH_DOUBLE_QUOTE, accuracy=.01)
        new_schedule.format_field("ACTUAL_Depth", display_units=DB.DisplayUnitType.DUT_DECIMAL_INCHES, symbol=DB.UnitSymbolType.UST_INCH_DOUBLE_QUOTE, accuracy=.01)
        new_schedule.format_field("ACTUAL_Height", display_units=DB.DisplayUnitType.DUT_DECIMAL_INCHES, symbol=DB.UnitSymbolType.UST_INCH_DOUBLE_QUOTE, accuracy=.01)
        new_schedule.format_field("TOTAL_List Price", display_units=DB.DisplayUnitType.DUT_CURRENCY, symbol=DB.UnitSymbolType.UST_DOLLAR, accuracy=.01)
        new_schedule.add_filter_by_name("Manufacturer", DB.ScheduleFilterType.BeginsWith, "Southwest Solutions Group")
        new_schedule.add_filter_by_name("Room: Number", DB.ScheduleFilterType.Equal, "103")
        new_schedule.add_sort_by_name("SSG_Product Code", sort_order=DB.ScheduleSortOrder.Descending)
        new_schedule.add_sort_by_name("TOTAL_List Price")
        # new_schedule.show_grid_lines(False)
        table_body = new_schedule.get_table_body()
        table_header = new_schedule.get_table_header()
        table_summary = new_schedule.get_table_summary()
        table_footer = new_schedule.get_table_footer()
        
        # print(table_body.NumberOfColumns, table_body.NumberOfRows)
        # print(table_body.GetCellText(table_body.NumberOfRows - 1, table_body.NumberOfColumns - 1))
        # print(table_summary.GetCellText(0,0))
        # print(table_footer.GetCellText(0,0))
        
        options = DB.TableCellStyleOverrideOptions()
        options.HorizontalAlignment = True
        style = DB.TableCellStyle()
        style.SetCellStyleOverrideOptions(options)
        style.FontHorizontalAlignment = DB.HorizontalAlignmentStyle.Left
        for i in range(table_body.NumberOfColumns):
            table_body.SetCellStyle(0, i, style)
        for i in range(table_header.NumberOfColumns):
            table_header.SetCellStyle(0, i, style)


        
        
# with revit.Transaction("Create room schedules"):    
#     for room in rooms:
#         room_name = room.get_Parameter(DB.BuiltInParameter.ROOM_NAME).AsString()
#         new_schedule = duplicate_schedule(my_schedule, new_name="{} {} Equipment Schedule".format(room.Number, room_name))
#         fields = get_fields(my_schedule)
#         room_num_field = next(iter([f for f in fields if f.GetName() == "Room: Number"]), None)
#         if room_num_field:
#             filt = DB.ScheduleFilter(
#                 room_num_field.FieldId,
#                 DB.ScheduleFilterType.Equal,
#                 room.Number
#             )
#             new_schedule.Definition.AddFilter(filt)
'''
