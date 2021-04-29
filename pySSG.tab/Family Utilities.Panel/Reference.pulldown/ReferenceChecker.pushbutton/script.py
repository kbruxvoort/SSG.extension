import clr
import Autodesk

clr.AddReference("RevitAPI")
# from Autodesk.Revit.DB import FilteredElementCollector
from pyrevit import revit, DB, UI
from pyrevit import script

# from pyrevit import forms

from Autodesk.Revit.Exceptions import ArgumentException, InvalidOperationException

logger = script.get_logger()

col = DB.FilteredElementCollector(revit.doc).OfClass(DB.ReferencePlane).ToElements()

named_ref, weak_ref, not_ref = [], [], []

with revit.Transaction("Create Subcategory"):
    ref_plane_cat = col[0].Category

    subCats = ref_plane_cat.SubCategories

    subNames = []
    if subCats:
        for sub in subCats:
            if sub.Name == "Named References":
                named_subcat_id = sub.Id
            elif sub.Name == "Weak References":
                weak_subcat_id = sub.Id
            elif sub.Name == "Not References":
                not_subcat_id = sub.Id
            subNames.append(sub.Name)

    try:
        if "Named References" not in subNames:
            named_subcat = revit.doc.Settings.Categories.NewSubcategory(
                ref_plane_cat, "Named References"
            )
            named_subcat.LineColor = DB.Color(128, 0, 255)
            named_subcat.SetLinePatternId(
                ref_plane_cat.GetLinePatternId(DB.GraphicsStyleType.Projection),
                DB.GraphicsStyleType.Projection,
            )
            named_subcat_id = named_subcat.Id
        if "Weak References" not in subNames:
            weak_subcat = revit.doc.Settings.Categories.NewSubcategory(
                ref_plane_cat, "Weak References"
            )
            weak_subcat.LineColor = DB.Color(255, 0, 128)
            # weak_subcat.SetLineWeight(5, DB.GraphicsStyleType.Projection)
            weak_subcat.SetLinePatternId(
                ref_plane_cat.GetLinePatternId(DB.GraphicsStyleType.Projection),
                DB.GraphicsStyleType.Projection,
            )
            weak_subcat_id = weak_subcat.Id
        if "Not References" not in subNames:
            not_subcat = revit.doc.Settings.Categories.NewSubcategory(
                ref_plane_cat, "Not References"
            )
            not_subcat.LineColor = DB.Color(225, 225, 255)
            not_subcat.SetLinePatternId(
                ref_plane_cat.GetLinePatternId(DB.GraphicsStyleType.Projection),
                DB.GraphicsStyleType.Projection,
            )
            not_subcat_id = not_subcat.Id

        for c in col:

            if (
                c.get_Parameter(
                    DB.BuiltInParameter.ELEM_REFERENCE_NAME_2D_XZ
                ).AsValueString()
                == "Not a Reference"
            ):
                not_ref.append(c)

            elif (
                c.get_Parameter(
                    DB.BuiltInParameter.ELEM_REFERENCE_NAME_2D_XZ
                ).AsValueString()
                == "Weak Reference"
            ):
                weak_ref.append(c)

            else:
                named_ref.append(c)

        print("%s: Named References" % str(len(named_ref)))
        print("%s: Not References" % str(len(not_ref)))

        if named_ref:
            for r in named_ref:
                param = r.get_Parameter(DB.BuiltInParameter.CLINE_SUBCATEGORY)
                param.Set(named_subcat_id)

        if weak_ref:
            message = "%s: Weak References" % str(len(weak_ref))
            print(logger.warning(message))
            for r in weak_ref:
                param = r.get_Parameter(DB.BuiltInParameter.CLINE_SUBCATEGORY)
                param.Set(weak_subcat_id)
        else:
            message = "Good job removing all those weak references"
            print(logger.success(message))

        if not_ref:
            for r in not_ref:
                param = r.get_Parameter(DB.BuiltInParameter.CLINE_SUBCATEGORY)
                param.Set(not_subcat_id)

    except InvalidOperationException:
        print("Subcategory Name already Exists")
