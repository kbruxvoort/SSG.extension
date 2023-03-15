from System.Collections.Generic import List
from pyrevit import revit, DB, forms
from utils import isclose

import dimension_config

def create_dimension(instance):
    left_ref, right_ref = None, None
    left_refs = instance.GetReferences(DB.FamilyInstanceReferenceType.Left)
    if left_refs:
        left_ref = left_refs[0]
    right_refs = instance.GetReferences(DB.FamilyInstanceReferenceType.Right)
    if right_refs:
        right_ref = right_refs[0]
    if not left_ref or not right_ref:
        return
    else:
        ref_array = DB.ReferenceArray()
        bbox = instance.get_BoundingBox(revit.doc.ActiveView)
        ref_array.Append(left_ref)
        ref_array.Append(right_ref)
        # back left
        dim_start = DB.XYZ(bbox.Min.X, bbox.Max.Y, 0)
        # back right
        dim_end = DB.XYZ(bbox.Max.X, bbox.Max.Y, 0)
        dim_line = DB.Line.CreateBound(dim_start, dim_end)
        dimension = revit.doc.Create.NewDimension(revit.doc.ActiveView, dim_line, ref_array)
        return dimension

def ask_for_options():
    element_cats = dimension_config.load_configs()
    
    all_text = "ALL LISTED CATEGORIES"
    select_options = [all_text] + sorted(x.Name for x in element_cats)
    selected_switch = forms.CommandSwitchWindow.show(
        select_options, message="Select Category to Dimension"
    )
    
    if selected_switch:
        if selected_switch == all_text:
            multi_cat_filt = DB.ElementMulticategoryFilter(List[DB.BuiltInCategory]([revit.query.get_builtincategory(cat) for cat in select_options if cat != all_text]))
            return (
                DB.FilteredElementCollector(revit.doc, revit.doc.ActiveView.Id)
                .WherePasses(multi_cat_filt)
                .ToElements()
            )
        else:
            return (
                DB.FilteredElementCollector(revit.doc, revit.doc.ActiveView.Id)
                .OfCategory(revit.query.get_builtincategory(selected_switch))
                .WhereElementIsNotElementType()
                .ToElements()
            )
    
    
family_instances = ask_for_options()
if family_instances:
    with revit.Transaction("Auto Dimension"):
        for f in family_instances:
            if not f.SuperComponent:
                create_dimension(f)
        
    # count = 0
    # while count + 1 < len(family_instances):
    #     left_instance = family_instances[count]
    #     right_instance = family_instances[count+1]
    #     if left_instance.Host != None or right_instance.Host != None: # skip nested families
    #         continue
    #     create_dimension(left_instance, right_instance)
    #     count += 1

'''
def get_instance_references(family_instance, view):
    # if perpendicular to view direction then use left/right, if parallel use front/back
    reference_array = DB.ReferenceArray()
    dp = view.ViewDirection.DotProduct(family_instance.FacingOrientation)
    left_references = family_instance.GetReferences(DB.FamilyInstanceReferenceType.Left)
    right_references = family_instance.GetReferences(DB.FamilyInstanceReferenceType.Right)
    back_references = family_instance.GetReferences(DB.FamilyInstanceReferenceType.Back)
    front_references = family_instance.GetReferences(DB.FamilyInstanceReferenceType.Front)
    if view.ViewType == DB.ViewType.Elevation or DB.ViewType.Section:
        if isclose(abs(dp), 1, abs_tol=.0001):
            if left_references:
                reference_array.Append(left_references[0])
            if right_references:
                reference_array.Append(right_references[0])
        elif isclose(abs(dp), 0, abs_tol=.0001):
            if back_references:
                reference_array.Append(back_references[0])
            if front_references:
                reference_array.Append(front_references[0])
    elif view.ViewType == DB.ViewType.FloorPlan:
        if left_references:
                reference_array.Append(left_references[0])
        if right_references:
            reference_array.Append(right_references[0])
    return(reference_array)


view = revit.doc.ActiveView

col = DB.FilteredElementCollector(revit.doc, view.Id).OfCategory(DB.BuiltInCategory.OST_Casework).OfClass(DB.FamilyInstance).ToElements()

# use bounding box to determine farthest left, right, top, bottom objects
# origin for line creation should be based on min/max points of all instances so dimensions align
if col:
    with revit.Transaction("Create Dimensions"):
        min_list, max_list = [], []
        down_shift = DB.UnitUtils.ConvertToInternalUnits(400, DB.DisplayUnitType.DUT_MILLIMETERS)
        up_shift = DB.UnitUtils.ConvertToInternalUnits(150, DB.DisplayUnitType.DUT_MILLIMETERS)
        for c in col:
            if not c.SuperComponent:
                refs = get_instance_references(c, view)
                bbox = c.get_BoundingBox(view)
                if refs.Size > 1:
                    if bbox.Min.Z < .01:
                        dim_start = DB.XYZ(bbox.Min.X, bbox.Max.Y - down_shift, 0)
                        dim_end = DB.XYZ(bbox.Max.X, bbox.Max.Y - down_shift, 0)
                    else:
                        dim_start = DB.XYZ(bbox.Min.X, bbox.Max.Y + up_shift, 0)
                        dim_end = DB.XYZ(bbox.Max.X, bbox.Max.Y + up_shift, 0)
                    dim_line = DB.Line.CreateUnbound(dim_start, dim_end)
                    dimension = revit.doc.Create.NewDimension(view, dim_line, refs)          

'''