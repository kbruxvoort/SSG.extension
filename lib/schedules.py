from pyrevit import revit, DB
from pyssg_utils import to_list


FILTER_TYPES = {
    "HasParameter": DB.ScheduleFilterType.HasParameter,
    "Equal": DB.ScheduleFilterType.Equal,
    "NotEqual": DB.ScheduleFilterType.NotEqual,
    "GreaterThan": DB.ScheduleFilterType.GreaterThan,
    "GreaterThanOrEqual": DB.ScheduleFilterType.GreaterThanOrEqual,
    "LessThan": DB.ScheduleFilterType.LessThan,
    "LessThanOrEqual": DB.ScheduleFilterType.LessThanOrEqual,
    "Contains": DB.ScheduleFilterType.Contains,
    "NotContains": DB.ScheduleFilterType.NotContains,
    "BeginsWith": DB.ScheduleFilterType.BeginsWith,
    "NotBeginsWith": DB.ScheduleFilterType.NotBeginsWith,
    "EndsWith": DB.ScheduleFilterType.EndsWith,
    "NotEndsWith": DB.ScheduleFilterType.NotEndsWith
}

class ScheduleWrapper(object):
    def __init__(self, schedule):
        self.schedule = schedule
    
    @classmethod
    def create(
        cls, 
        doc, 
        category_id=None, 
        name=None, 
        itemized=False,
        show_grand_total=False,
        show_grand_total_title=False,
        grand_total_title=None,
        show_total_count=False,
        show_headers=True,
        show_title=True,
    ):
        if not category_id:
            category_id = DB.ElementId.InvalidElementId
        schedule = DB.ViewSchedule.CreateSchedule(doc, category_id)
        if name:
            schedule.Name = name
        schedule.Definition.IsItemized = itemized
        schedule.Definition.ShowGrandTotal = show_grand_total
        schedule.Definition.ShowHeaders = show_headers
        schedule.Definition.ShowTitle = show_title
        if show_grand_total is True:
            schedule.Definition.ShowGrandTotalCount = show_total_count
            schedule.Definition.ShowGrandTotalTitle = show_grand_total_title
            if show_grand_total_title is True:
                schedule.Definition.GrandTotalTitle = grand_total_title
            
        return cls(schedule)
    
    @classmethod
    def duplicate(cls, doc, schedule, new_name=None):
        new_schedule_id = schedule.Duplicate(DB.ViewDuplicateOption.Duplicate)
        new_schedule = doc.GetElement(new_schedule_id)
        if new_name:
            new_schedule.Name = new_name
        else:
            new_schedule.Name = schedule.Name + " Copy"
        return cls(new_schedule)
    
    # Fields
    def get_schedulable_fields(self):
        return self.schedule.Definition.GetSchedulableFields()
    
    def get_fields(self):
        field_ids = self.schedule.Definition.GetFieldOrder()
        return [self.schedule.Definition.GetField(field_id) for field_id in field_ids]

    def get_fields_by_name(self, name_list):
        fields = self.get_fields()
        return [f for f in fields if f.GetName() in name_list]
    
    def add_field(
        self, 
        field_name, 
        heading=None, 
        width=None, 
        heading_orientation=DB.ScheduleHeadingOrientation.Horizontal, 
        alignment=DB.ScheduleHorizontalAlignment.Left,
        hidden=False,
        unit_type=None,
        calculate_totals=False,
    ):
        possible_fields = self.get_schedulable_fields()
        for pf in possible_fields:
            if field_name == pf.GetName(revit.doc):
                new_field = self.schedule.Definition.AddField(pf)
                if heading:
                    new_field.ColumnHeading = heading
                if width:
                    new_field.GridColumnWidth = width
                if heading_orientation:
                    new_field.HeadingOrientation = heading_orientation
                if alignment:
                    new_field.HorizontalAlignment = alignment
                if hidden is True:
                    new_field.IsHidden = True
                if new_field.CanTotal() and calculate_totals:
                    new_field.DisplayType = DB.ScheduleFieldDisplayType.Totals
                return new_field
    
    # def add_calculated_field(self)
    
    def add_fields(self, field_list):
        possible_fields = self.get_schedulable_fields()
        for f in field_list:
            for pf in possible_fields:
                if f == pf.GetName(revit.doc):
                    self.schedule.Definition.AddField(pf)
                    break
                    
    def insert_field(self, field_name, index=0):
        possible_fields = self.get_schedulable_fields()
        for pf in possible_fields:
            if field_name == pf.GetName(revit.doc):
                self.schedule.Definition.InsertField(pf, index)
                
    def remove_field(self, field_name):
        field = next(iter(self.get_fields_by_name([field_name])), None)
        if field:
            self.schedule.Definition.RemoveField(field.FieldId)
            
    def format_field(self, field_name, display_units=None, symbol=None, accuracy=None):
        field = next(iter(self.get_fields_by_name([field_name])), None)
        if field:
                format_options = DB.FormatOptions()
                if any([display_units, symbol, accuracy]):
                    format_options.UseDefault = False
                    if display_units:
                        format_options.DisplayUnits = display_units
                    if symbol and format_options.IsValidUnitSymbol(symbol):
                        format_options.UnitSymbol = symbol
                    if accuracy and format_options.IsValidAccuracy(accuracy):
                        format_options.Accuracy = accuracy
                        
                    field.SetFormatOptions(format_options)
                    return field

    
    # Filter
    def create_filter(self, field_id, filter_type, value=None):
        if value:
            return DB.ScheduleFilter(field_id, filter_type, value)
        else:
            return DB.ScheduleFilter(field_id, filter_type)
        
    def create_filter_by_name(self, field_name, filter_type, value=None):
        field_name = to_list(field_name)
        field = next(iter(self.get_fields_by_name(field_name)), None)
        if field:
            return self.create_filter(field.FieldId, filter_type, value)
        
    def add_filter_by_name(self, field_name, filter_type_name, value=None):
        filt = self.create_filter_by_name(field_name, filter_type_name, value)
        if filt:
            self.add_filter(filt)

    def add_filter(self, schedule_filter):
        self.schedule.Definition.AddFilter(schedule_filter)
    
    def set_filter(self, schedule_filter, index=0):
        self.schedule.Definition.SetFilter(index, schedule_filter)
        
    def remove_filter(self, index=0):
        self.schedule.Definition.RemoveFilter(index)
    
    # Sorting/Grouping
    def add_sort_by_name(
        self, 
        field_name, 
        sort_order=DB.ScheduleSortOrder.Ascending, 
        show_blank_line=False, 
        show_footer=False, 
        show_footer_count=False, 
        show_footer_title=False, 
        show_header=False
    ):
        field_name = to_list(field_name)
        field = next(iter(self.get_fields_by_name(field_name)), None)
        if field:
            sort_group = DB.ScheduleSortGroupField(field.FieldId, sort_order)
            sort_group.ShowBlankLine = show_blank_line
            sort_group.ShowHeader = show_header
            sort_group.ShowFooter = show_footer
            if show_footer:
                sort_group.ShowFooterCount = show_footer_count
                sort_group.ShowFooterTitle = show_footer_title
            self.schedule.Definition.AddSortGroupField(sort_group)
                
        
    def set_sort_field(self, field):
        field_index = self.schedule.Definition.GetFieldIndex(field)
        self.schedule.Definition.SetSortGroupField(field_index)
    
    def set_sort_order(self, ascending):
        sort_order = DB.SortingOrder.Ascending if ascending else DB.SortingOrder.Descending
        self.schedule.Definition.SetSortOrder(sort_order)
    
    def get_data_table(self):
        data_table = self.schedule.GetTableData().GetSectionData(DB.SectionType.Body).GetCellTexts()
        return data_table
    
    # Appearance
    def get_table_header(self):
        return self.schedule.GetTableData().GetSectionData(DB.SectionType.Header)
    
    def get_table_footer(self):
        return self.schedule.GetTableData().GetSectionData(DB.SectionType.Footer)
    
    def get_table_summary(self):
        return self.schedule.GetTableData().GetSectionData(DB.SectionType.Summary)
    
    def get_table_body(self):
        return self.schedule.GetTableData().GetSectionData(DB.SectionType.Body)
    
    def set_body_text(self, text_note_type_id):
        self.BodyTextTypeId = text_note_type_id
        
    def set_header_text(self, text_note_type_id):
        self.HeaderTextTypeId = text_note_type_id
        
    def set_title_text(self, text_note_type_id):
        self.TitleTextTypeId = text_note_type_id
        
    def show_total(self, IsShown=True):
        self.schedule.Definition.ShowGrandTotal = IsShown
        
    def show_total_count(self, IsShown=True):
        self.schedule.Definition.ShowGrandTotalCount = IsShown
        
    def show_total_title(self, IsShown=True):
        self.schedule.Definition.ShowGrandTotalTitle = IsShown
        
    def show_grid_lines(self, IsShown=True):
        self.schedule.Definition.ShowGridLines = IsShown
        
    def show_headers(self, IsShown=True):
        self.schedule.Definition.ShowHeaders = IsShown
        
    def show_title(self, IsShown=True):
        self.schedule.Definition.ShowTitle = IsShown
    # TableData Width/WidthInPixels
    # self.BodyTextTypeId
    # self.HeaderTextTypeId
    # self.TitleTextTypeId
    # TextNoteType.get_Parameter(DB.BuiltInParameter.TEXT_FONT).AsString() == "Seogoe UI"
    # TextNoteType.get_Parameter(DB.BuiltInParameter.TEXT_SIZE).AsDouble() == 0.00520833333333333
    # TextNoteType.get_Parameter(DB.BuiltInParameter.LINE_COLOR).AsInteger() == 6179124
    def create_body_text(self):
        text_note_type_id = None
        self.set_body_text(text_note_type_id)