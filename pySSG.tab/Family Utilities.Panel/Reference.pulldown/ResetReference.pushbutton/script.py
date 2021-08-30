from pyrevit import revit, DB


from Autodesk.Revit.Exceptions import InvalidOperationException

col = DB.FilteredElementCollector(revit.doc).OfClass(DB.ReferencePlane).ToElements()

with revit.Transaction("Create Subcategory"):
    ref_plane_cat = col[0].Category

    try:
        for r in col:
            param = r.get_Parameter(DB.BuiltInParameter.CLINE_SUBCATEGORY)
            param.Set(ref_plane_cat.Id)

    except InvalidOperationException:
        print("Subcategory Name already Exists")
