from pyrevit import revit, DB, script

my_config = script.get_config("override cropbox")
line_weight = my_config.get_option("line_weight", 6) 

ogs = DB.OverrideGraphicSettings().SetProjectionLineWeight(int(line_weight))
view_sections = DB.FilteredElementCollector(revit.doc).OfClass(DB.ViewSection).ToElements()

with revit.Transaction("Override Crop Lineweight"):
    for v in view_sections:
        if not v.IsTemplate:
            if v.ViewType == DB.ViewType.Elevation:
                crop_id = DB.ElementId(int(v.Id.ToString())-1)
                v.CropBoxActive = True
                v.CropBoxVisible = True
                v.SetElementOverrides(crop_id, ogs)
