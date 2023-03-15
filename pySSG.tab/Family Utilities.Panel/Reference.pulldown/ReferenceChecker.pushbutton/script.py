from System.Collections.Generic import List
from pyrevit import revit, DB


from Autodesk.Revit.Exceptions import ArgumentException

ref_styles = {
    "pySSG_strong": {"color": DB.Color(127, 46, 45), "pattern": (1, .125/12)},
    "pySSG_weak": {"color": DB.Color(208, 75, 74), "pattern": (.5/12, .125/12)},
    "pySSG_not_ref": {"color": DB.Color(250, 237, 237), "pattern": (.25/12, .125/12)}
}

references = DB.FilteredElementCollector(revit.doc).OfClass(DB.ReferencePlane).ToElements()
if references:
    ref_cat = references[0].Category
    ref_subcats = ref_cat.SubCategories
    line_pattern_elements = DB.FilteredElementCollector(revit.doc).OfClass(DB.LinePatternElement).ToElements()
    
    
    with revit.Transaction("Check References"):
        # create line patterns
        pattern_dict = {}
        for k,v in ref_styles.items():
            pat_elem = DB.LinePatternElement.GetLinePatternElementByName(revit.doc, k)
            segments = List[DB.LinePatternSegment]()
            segments.Add(DB.LinePatternSegment(DB.LinePatternSegmentType.Dash, v["pattern"][0]))
            segments.Add(DB.LinePatternSegment(DB.LinePatternSegmentType.Space, v["pattern"][1]))
            
            if pat_elem:
                pattern = pat_elem.GetLinePattern()
                pattern.SetSegments(segments)
                pat_elem.SetLinePattern(pattern)
            else:
                pattern = DB.LinePattern(k)
                pattern.SetSegments(segments)
                try:
                    pat_elem = DB.LinePatternElement.Create(revit.doc, pattern)
                except ArgumentException as ae:
                    print("Unable to create line pattern: {}".format(ae))
                    raise NameError
            if pat_elem:
                subcat_list = [sc for sc in ref_subcats if sc.Name == k]
                if subcat_list:
                    subcat = subcat_list[0]
                else:
                    subcat = revit.doc.Settings.Categories.NewSubcategory(ref_cat, k)
                subcat.LineColor = v["color"]
                subcat.SetLinePatternId(
                    pat_elem.Id,
                    DB.GraphicsStyleType.Projection,
                )
                ref_styles[k]["subcategory"] = subcat.Id
                
        for ref in references:
            ref_subcat_param = ref.get_Parameter(DB.BuiltInParameter.CLINE_SUBCATEGORY)
            is_ref = ref.get_Parameter(DB.BuiltInParameter.ELEM_REFERENCE_NAME)

            if is_ref.AsInteger() < 9 or is_ref.AsInteger() == 13:
                ref_subcat_param.Set(ref_styles["pySSG_strong"]["subcategory"])
            elif is_ref.AsInteger() == 14:
                ref_subcat_param.Set(ref_styles["pySSG_weak"]["subcategory"])
            elif is_ref.AsInteger() == 12:
                ref_subcat_param.Set(ref_styles["pySSG_not_ref"]["subcategory"])
                
        revit.active_view.HideCategoryTemporary(DB.ElementId(DB.BuiltInCategory.OST_Dimensions.GetHashCode()))
