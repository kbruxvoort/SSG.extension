from pyrevit import revit, DB
from collect import get_placed_rooms
from schedules import ScheduleWrapper
from text_notes import TextType
from color import Color




schedule_name = "SSG_Master Schedule"

rooms = get_placed_rooms(revit.doc)
schedules = revit.query.get_all_schedules(revit.doc)

equip_schedule = next(iter([s for s in schedules if s.Name == schedule_name]), None)



if not equip_schedule:
    # Create schedule
    with revit.Transaction("Create Schedule"):
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
        
        my_schedule = ScheduleWrapper.create(revit.doc, name="SSG Equipment Schedule", show_grand_total=True, show_grand_total_title=True, grand_total_title="Grand Total:")
        for f in field_list:
            my_schedule.add_field(f.get("field_name"), heading=f.get("heading"), width=f.get("width"), alignment=f.get("alignment"), hidden=f.get("hidden", False), calculate_totals=f.get("calculate_totals", False))
        my_schedule.format_field("ACTUAL_Width", display_units=DB.DisplayUnitType.DUT_DECIMAL_INCHES, symbol=DB.UnitSymbolType.UST_INCH_DOUBLE_QUOTE, accuracy=.01)
        my_schedule.format_field("ACTUAL_Depth", display_units=DB.DisplayUnitType.DUT_DECIMAL_INCHES, symbol=DB.UnitSymbolType.UST_INCH_DOUBLE_QUOTE, accuracy=.01)
        my_schedule.format_field("ACTUAL_Height", display_units=DB.DisplayUnitType.DUT_DECIMAL_INCHES, symbol=DB.UnitSymbolType.UST_INCH_DOUBLE_QUOTE, accuracy=.01)
        my_schedule.format_field("TOTAL_List Price", display_units=DB.DisplayUnitType.DUT_CURRENCY, symbol=DB.UnitSymbolType.UST_DOLLAR, accuracy=.01)
        my_schedule.add_filter_by_name("Manufacturer", DB.ScheduleFilterType.BeginsWith, "Southwest Solutions Group")
        # my_schedule.add_filter_by_name("Room: Number", DB.ScheduleFilterType.Equal, "103")
        my_schedule.add_sort_by_name("SSG_Product Code", sort_order=DB.ScheduleSortOrder.Descending)
        my_schedule.add_sort_by_name("TOTAL_List Price")
        
        table_body = my_schedule.get_table_body()
        table_header = my_schedule.get_table_header()
        
        options = DB.TableCellStyleOverrideOptions()
        options.HorizontalAlignment = True
        style = DB.TableCellStyle()
        style.SetCellStyleOverrideOptions(options)
        style.FontHorizontalAlignment = DB.HorizontalAlignmentStyle.Left
        for i in range(table_body.NumberOfColumns):
            table_body.SetCellStyle(0, i, style)
        for i in range(table_header.NumberOfColumns):
            table_header.SetCellStyle(0, i, style)

else:
    my_schedule = ScheduleWrapper(equip_schedule)

        
        
with revit.Transaction("Create room schedules"):    
    for room in rooms:
        room_name = room.get_Parameter(DB.BuiltInParameter.ROOM_NAME).AsString()
        room_schedule = ScheduleWrapper.duplicate(revit.doc, my_schedule.schedule, new_name="{} {} Equipment Schedule".format(room.Number, room_name))
        room_schedule.add_filter_by_name("Room: Number", DB.ScheduleFilterType.Equal, value=room.Number)

