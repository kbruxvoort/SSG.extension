from System.Collections.Generic import List
from pyrevit import revit, DB, forms
from pyssg_utils import isclose

import dimension_config

def get_instance_refs(family_instance):
    references = {}
    unwanted_ref_types = [
        DB.FamilyInstanceReferenceType.StrongReference,
        DB.FamilyInstanceReferenceType.WeakReference,
        DB.FamilyInstanceReferenceType.NotAReference
    ]
    family_instance_reference_types = list(DB.FamilyInstanceReferenceType.GetValues(DB.FamilyInstanceReferenceType))
    for ref_type in family_instance_reference_types:
        if ref_type not in unwanted_ref_types:
            ref_list = family_instance.GetReferences(ref_type)
            if ref_list:
                references[str(ref_type)] = ref_list[0]
                
    return references
    
def get_block_box_and_axis(family_instances, view=None):
    x_pts = []
    y_pts = []
    z_pts = []
    for instance in family_instances:
        inst_bbox = instance.get_BoundingBox(view)
        x_pts.append(inst_bbox.Min.X)
        x_pts.append(inst_bbox.Max.X)
        y_pts.append(inst_bbox.Min.Y)
        y_pts.append(inst_bbox.Max.Y)
        z_pts.append(inst_bbox.Min.Z)
        z_pts.append(inst_bbox.Max.Z)
    
    max_x = max(x_pts)
    max_y = max(y_pts)
    max_z = max(z_pts)
    min_x = min(x_pts)
    min_y = min(y_pts)
    min_z = min(z_pts)
    
    bbox = DB.BoundingBoxXYZ()
    bbox.Min = DB.XYZ(min_x, min_y, min_z)
    bbox.Max = DB.XYZ(max_x, max_y, max_z)
    axis = determine_long_axis(max_x, min_x, max_y, min_y)
    
    return bbox, axis

def determine_long_axis(max_x, min_x, max_y, min_y):
    if max_y - min_y > max_x - min_x:
        return "Y"
    else:
        return "X"
    
def find_outside_instances(document, family_instances, tolerance=0.084):
    # outside_instances = []
    left_instances = []
    right_instances = []
    
    block_bbox, long_axis = get_block_box_and_axis(family_instances, document.ActiveView)

    for instance in family_instances:
        bounding_box = instance.get_BoundingBox(document.ActiveView)
        if bounding_box:
            min_point = bounding_box.Min
            max_point = bounding_box.Max

            if long_axis == "X":
                if abs(block_bbox.Min.X - min_point.X) <= tolerance:
                    left_instances.append(instance)
                if abs(block_bbox.Max.X - max_point.X) <= tolerance:
                    right_instances.append(instance)
                    
            elif long_axis == "Y":
                if abs(block_bbox.Min.Y - min_point.Y) <= tolerance:
                    left_instances.append(instance)
                if abs(block_bbox.Max.Y - max_point.Y) <= tolerance:
                    right_instances.append(instance)
                    
    return (left_instances, right_instances)


          

def create_dimension(document, family_instances):
    PLAN_TYPES = [
        DB.ViewType.FloorPlan,
        DB.ViewType.CeilingPlan,
        DB.ViewType.AreaPlan,
    ]
    ELELVATION_TYPES = [
        DB.ViewType.Elevation,
        DB.ViewType.Section
    ]
    OFFSET_VALUE = 1
    
    if document.ActiveView.ViewType in PLAN_TYPES:
        # All instances get left, right
        for family_instance in family_instances:
            if family_instance.SuperComponent is None:
                ref_dict = get_instance_refs(family_instance)
                orientation = family_instance.FacingOrientation
                
                if ref_dict.get('Left') and ref_dict.get('Right'):
                    ref_array_1 = DB.ReferenceArray()
                    offset = orientation.Multiply(OFFSET_VALUE)
                    pt2_direction = DB.XYZ(-orientation.Y, orientation.X, 0)
                    ref_array_1.Append(ref_dict.get('Left'))
                    ref_array_1.Append(ref_dict.get('Right'))
                    dim_line_1 = DB.Line.CreateUnbound(family_instance.Location.Point.Add(offset), pt2_direction)
                    dimension_1 = document.Create.NewDimension(document.ActiveView, dim_line_1, ref_array_1)
        
        left_instances, right_instances = find_outside_instances(document, family_instances)
        for left in left_instances:
            ref_dict = get_instance_refs(left)
            orientation = left.FacingOrientation
            if ref_dict.get('Front') and ref_dict.get('Back'):
                ref_array_2 = DB.ReferenceArray()
                offset_direct = DB.XYZ(orientation.Y, orientation.X, 0)
                offset = offset_direct.Multiply(OFFSET_VALUE)
                ref_array_2.Append(ref_dict.get('Front'))
                ref_array_2.Append(ref_dict.get('Back'))
                test = DB.XYZ(orientation.Y, orientation.X, orientation.Z)
                pt = left.get_BoundingBox(document.ActiveView)
                dim_line_2 = DB.Line.CreateUnbound(pt.Min.Subtract(offset), orientation)
                dimension_2 = document.Create.NewDimension(document.ActiveView, dim_line_2, ref_array_2)
                
        for right in right_instances:
            ref_dict = get_instance_refs(right)
            orientation = right.FacingOrientation
            if ref_dict.get('Front') and ref_dict.get('Back'):
                ref_array_3 = DB.ReferenceArray()
                offset_direct = DB.XYZ(orientation.Y, orientation.X, 0)
                offset = offset_direct.Multiply(-OFFSET_VALUE)
                ref_array_3.Append(ref_dict.get('Front'))
                ref_array_3.Append(ref_dict.get('Back'))
                test = DB.XYZ(orientation.Y, orientation.X, orientation.Z)
                pt = right.get_BoundingBox(document.ActiveView)
                dim_line_3 = DB.Line.CreateUnbound(pt.Max.Add(offset), orientation)
                dimension_3 = document.Create.NewDimension(document.ActiveView, dim_line_3, ref_array_3)
    
    elif document.ActiveView.ViewType in ELELVATION_TYPES:
        view_direction = document.ActiveView.ViewDirection
        for family_instance in family_instances:
            if family_instance.SuperComponent is None:
                bbox = family_instance.get_BoundingBox(document.ActiveView)
                ref_dict = get_instance_refs(family_instance)
                orientation = family_instance.FacingOrientation
                
                dot_product = view_direction.DotProduct(orientation)
                threshold = .01
                ref_1 = None
                ref_2 = None
                ref_array_3 = DB.ReferenceArray()
                
                # family is perpendicular to view
                if abs(dot_product) < threshold:
                    if ref_dict.get('Front') and ref_dict.get('Back'):
                        ref_1 = ref_dict.get('Front')
                        ref_2 = ref_dict.get('Back')
                        
                # family is parallel to view
                elif abs(dot_product) > 1 - threshold:
                    if ref_dict.get('Left') and ref_dict.get('Right'):
                        ref_1 = ref_dict.get('Left')
                        ref_2 = ref_dict.get('Right')
                        
                if ref_1 and ref_2:
                        
                    if bbox.Min.Z < 1:
                        offset_value = 1.5
                        offset = DB.XYZ.BasisZ.Multiply(-offset_value)
                        pt1 = family_instance.Location.Point.Add(offset)
                    else:
                        offset_value = .5
                        offset = DB.XYZ.BasisZ.Multiply(offset_value)
                        pt1 = bbox.Max.Add(offset)

                    ref_array_3.Append(ref_1)
                    ref_array_3.Append(ref_2)
                    test = DB.XYZ(-view_direction.Y, view_direction.X, 0)
                    dim_line_3 = DB.Line.CreateUnbound(pt1, test)
                    dimension_3 = document.Create.NewDimension(document.ActiveView, dim_line_3, ref_array_3)
        
        left_instances, right_instances = find_outside_instances(document, family_instances)
        for left in left_instances:
            bbox = left.get_BoundingBox(document.ActiveView)
            ref_dict = get_instance_refs(left)
            orientation = left.FacingOrientation
            view_direction = document.ActiveView.ViewDirection
            ref_array_4 = DB.ReferenceArray()
            if ref_dict.get('Bottom') and ref_dict.get('Top'):
                ref_1 = ref_dict.get('Bottom')
                ref_2 = ref_dict.get('Top')
                ref_array_4.Append(ref_1)
                ref_array_4.Append(ref_2)
                offset = DB.XYZ.BasisX.Multiply(OFFSET_VALUE)
                pt1 = bbox.Min.Subtract(offset)
                dim_line_4 = DB.Line.CreateUnbound(pt1, DB.XYZ.BasisZ)
                dimension_4 = document.Create.NewDimension(document.ActiveView, dim_line_4, ref_array_4)
                
        for right in right_instances:
            bbox = right.get_BoundingBox(document.ActiveView)
            ref_dict = get_instance_refs(right)
            orientation = right.FacingOrientation
            view_direction = document.ActiveView.ViewDirection
            ref_array_5 = DB.ReferenceArray()
            if ref_dict.get('Bottom') and ref_dict.get('Top'):
                ref_1 = ref_dict.get('Bottom')
                ref_2 = ref_dict.get('Top')
                ref_array_5.Append(ref_1)
                ref_array_5.Append(ref_2)
                offset = DB.XYZ.BasisX.Multiply(OFFSET_VALUE)
                pt1 = bbox.Max.Add(offset)
                dim_line_5 = DB.Line.CreateUnbound(pt1, DB.XYZ.BasisZ)
                dimension_5 = document.Create.NewDimension(document.ActiveView, dim_line_5, ref_array_5)
            
def is_perpendicular(view_direction, instance_orientation, tolerance=.01):
    dot_product = view_direction.Normalize().DotProduct(instance_orientation.Normalize())
    if abs(dot_product) < tolerance:
        return True
    else:
        return False
    
def is_parallel(view_direction, instance_orientation, tolerance=.01):
    dot_product = view_direction.Normalize().DotProduct(instance_orientation.Normalize())
    if abs(dot_product) > 1 - tolerance:
        return True
    else:
        return False

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
        else:
            multi_cat_filt = DB.ElementMulticategoryFilter(List[DB.BuiltInCategory]([revit.query.get_builtincategory(selected_switch)]))
            
        if multi_cat_filt:
            return DB.FilteredElementCollector(revit.doc, revit.doc.ActiveView.Id) \
                                              .WherePasses(multi_cat_filt) \
                                              .ToElements()


        

family_instances = ask_for_options()
if family_instances:
    instance_blocks = []
    instance_ids = [instance.Id.ToString() for instance in family_instances if instance.SuperComponent is None]

    for _id in instance_ids:
        current_instance = revit.doc.GetElement(DB.ElementId(int(_id)))
        bbox = current_instance.get_BoundingBox(revit.doc.ActiveView)
        new_max_z = bbox.Max.Z + 3
        new_min_z = bbox.Min.Z - 3
        outline = DB.Outline(DB.XYZ(bbox.Min.X, bbox.Min.Y, new_min_z), DB.XYZ(bbox.Max.X, bbox.Max.Y, new_max_z))
        tolerance = .1
        bbox_filter = DB.BoundingBoxIntersectsFilter(outline, tolerance, False)
        collector = DB.FilteredElementCollector(revit.doc, revit.doc.ActiveView.Id)
        adjacent_instance_ids = collector.WherePasses(bbox_filter).WhereElementIsNotElementType().ToElementIds()
        filtered_adjacent_ids = [aj_id.ToString() for aj_id in adjacent_instance_ids if aj_id.ToString() in instance_ids]
        block_match = False
        
        for block in instance_blocks:
            if any(ajs in filtered_adjacent_ids for ajs in block):
                block.append(_id)
                block_match = True
                break
        if block_match is False:
            instance_blocks.append([_id])

    with revit.Transaction("Auto Dimension"):
        for block in instance_blocks:
            family_instances = [revit.doc.GetElement(DB.ElementId(int(_id))) for _id in block]
            
            if family_instances:
                create_dimension(revit.doc, family_instances)
