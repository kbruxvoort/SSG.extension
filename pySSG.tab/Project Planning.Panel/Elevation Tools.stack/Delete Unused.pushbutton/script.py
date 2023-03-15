from pyrevit import revit, forms, DB



# viewFamTypes = DB.FilteredElementCollector(revit.doc).OfClass(DB.ViewFamilyType).ToElements()

views = DB.FilteredElementCollector(revit.doc).OfClass(DB.ViewSection).ToElements()

# elems = []
# for t in viewFamTypes:
#     if "Interior Elevation" in DB.Element.Name.GetValue(t):
#         elems.append(t)

# viewType = elems[0]

with revit.TransactionGroup("Delete Unused Elevations"):
    with revit.Transaction("Delete Elevations"):
        count = 0
        for v in views:
            if v.GetTypeId() == revit.doc.GetDefaultElementTypeId(DB.ElementTypeGroup.ViewTypeElevation):
                param_id = DB.ElementId(DB.BuiltInParameter.ALL_MODEL_MANUFACTURER)
                param_prov = DB.ParameterValueProvider(param_id)
                param_begins = DB.FilterStringBeginsWith()
                value_rule = DB.FilterStringRule(
                    param_prov, 
                    param_begins, 
                    "Southwest Solutions Group", 
                    False
                )
                filt = DB.ElementParameterFilter(value_rule)
                fam = DB.FilteredElementCollector(revit.doc, v.Id) \
                                                .WhereElementIsNotElementType() \
                                                .WherePasses(filt) \
                                                .FirstElement()
                if not fam:
                    count += 1
                    revit.doc.Delete(v.Id)

    markers = DB.FilteredElementCollector(revit.doc) \
                                        .OfClass(DB.ElevationMarker) \
                                        .ToElements()
    with revit.Transaction("Delete empty markers"):
        for marker in markers:
            if marker.CurrentViewCount == 0:
                with revit.Transaction("Delete Unused Markers"):
                    revit.doc.Delete(marker.Id)

    forms.alert(msg="{} elevation(s) deleted".format(count))
