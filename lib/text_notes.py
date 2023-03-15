from Autodesk.Revit.Exceptions import ArgumentException

from pyrevit import DB, revit
from color import Color


class TextType(object):
    def __init__(self, text_type):
        self.text_type = text_type
    
    @classmethod
    def create(
        cls,
        doc=revit.doc, 
        name=None,
        is_transparent=True,
        bold=False,
        color=Color(0, 0, 0).int_value,
        italic=False,
        font="Arial",
        size=0.0078125,
        underline=False,
        width_factor=1,
        tab_size = None,
        #arrowhead
        #offset
        #lineweight
        #showborder 

    ):  
        if not name:
            options = DB.FormatValueOptions()
            options.AppendUnitSymbol = True
            
            font_size = DB.UnitFormatUtils.Format(
                doc.GetUnits(), 
                # DB.DisplayUnitType.DUT_DECIMAL_FEET, 
                DB.UnitType.UT_Length,
                size,
                False,
                False,
                options
                )
            name = "{} - {} - {}".format(font_size, font, Color(color).hexcode)
        text_note_type = DB.FilteredElementCollector(doc).OfClass(DB.TextNoteType).FirstElement()
        try:
            new_text = text_note_type.Duplicate(name)
        except ArgumentException:
            new_text = text_note_type.Duplicate(name + " (Copy)")
        color_param = new_text.get_Parameter(DB.BuiltInParameter.LINE_COLOR)
        color_param.Set(color)
        bg_param = new_text.get_Parameter(DB.BuiltInParameter.TEXT_BACKGROUND)
        bg_param.Set(is_transparent)
        bold_param = new_text.get_Parameter(DB.BuiltInParameter.TEXT_STYLE_BOLD)
        bold_param.Set(bold)
        italic_param = new_text.get_Parameter(DB.BuiltInParameter.TEXT_STYLE_ITALIC)
        italic_param.Set(italic)
        font_param = new_text.get_Parameter(DB.BuiltInParameter.TEXT_FONT)
        font_param.Set(font)
        font_size_param = new_text.get_Parameter(DB.BuiltInParameter.TEXT_SIZE)
        font_size_param.Set(size)
        underline_param = new_text.get_Parameter(DB.BuiltInParameter.TEXT_STYLE_UNDERLINE)
        underline_param.Set(underline)
        width_param = new_text.get_Parameter(DB.BuiltInParameter.TEXT_WIDTH_SCALE)
        width_param.Set(width_factor)
        tab_param = new_text.get_Parameter(DB.BuiltInParameter.TEXT_TAB_SIZE)
        if not tab_size:
            tab_size=size
        tab_param.Set(tab_size)
        return cls(new_text)
    
    @staticmethod
    def query(
        name=None,
        font=None,
        size=None,
        color=None,
        
    ):
        text_note_type = DB.FilteredElementCollector(doc).OfClass(DB.TextNoteType).ToElements()
        if name:
            text_note_type = [t for t in text_note_type if t.Name == name]
        if font:
            text_note_type = [t for t in text_note_type if t.get_Parameter(DB.BuiltInParameter.TEXT_FONT).AsString() == font]
        if size:
            text_note_type = [t for t in text_note_type if t.get_Parameter(DB.BuiltInParameter.TEXT_SIZE).AsDouble() == size]
        if color:
            text_note_type = [t for t in text_note_type if t.get_Parameter(DB.BuiltInParameter.LINE_COLOR).AsInteger() == color]
            
        return text_note_type

