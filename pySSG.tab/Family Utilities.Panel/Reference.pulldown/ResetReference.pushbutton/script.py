from pyrevit import revit, DB


ref_style_names = [
    "pySSG_strong",
    "pySSG_weak",
    "pySSG_not_ref",
]

references = DB.FilteredElementCollector(revit.doc).OfClass(DB.ReferencePlane).ToElements()
if references:
    ref_cat = references[0].Category

    with revit.Transaction("Reset References"):
        subcat_ids = []
        # turn off isolate
        if revit.active_view.IsTemporaryHideIsolateActive():
            revit.active_view.DisableTemporaryViewMode(
                DB.TemporaryViewMode.TemporaryHideIsolate
            )
        
        # remove subcategory from references
        for ref in references:
            param = ref.get_Parameter(DB.BuiltInParameter.CLINE_SUBCATEGORY)
            param.Set(ref_cat.Id)
        
        # delete subcategories and line patterns
        ref_subcats = ref_cat.SubCategories
        for name in ref_style_names:
            pattern_element = DB.LinePatternElement.GetLinePatternElementByName(revit.doc, name)
            if pattern_element:
                revit.doc.Delete(pattern_element.Id)

            # match subcats
            for subcat in ref_subcats:
                if subcat.Name == name:
                    subcat_ids.append(subcat.Id)
                    break
        
        # delete subcategories
        for _id in subcat_ids:
            revit.doc.Delete(_id)
   
        
        

                
        
            
        

