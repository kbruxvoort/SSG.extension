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

def determine_block_center(family_instances):
    location_pts = []
    for instance in family_instances:
        try:
            pt = instance.Location.Point
            location_pts.append(pt)
        except AttributeError:
            pass
    if location_pts:
        return sum(location_pts) / len(location_pts)
          

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
                    
                if ref_dict.get('Front') and ref_dict.get('Back'):
                    ref_array_2 = DB.ReferenceArray()
                    offset_direct = DB.XYZ(-orientation.Y, orientation.X, 0)
                    offset = offset_direct.Multiply(-OFFSET_VALUE)
                    ref_array_2.Append(ref_dict.get('Front'))
                    ref_array_2.Append(ref_dict.get('Back'))
                    test = DB.XYZ(orientation.Y, orientation.X, orientation.Z)
                    dim_line_2 = DB.Line.CreateUnbound(family_instance.Location.Point.Add(offset), orientation)
                    dimension_2 = document.Create.NewDimension(document.ActiveView, dim_line_2, ref_array_2)
    
    elif document.ActiveView.ViewType in ELELVATION_TYPES:
        for family_instance in family_instances:
            if family_instance.SuperComponent is None:
                bbox = family_instance.get_BoundingBox(document.ActiveView)
                ref_dict = get_instance_refs(family_instance)
                orientation = family_instance.FacingOrientation
                view_direction = document.ActiveView.ViewDirection
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
            
                # print('same perpendicular')

    
    # for segment in dimension.Segments:
    #     if isclose(segment.Value, 0):
    #         #delete segment
    #         pass

    # if ref_dict.get('Left') and ref_dict.get('Right'):
    #     offset = orientation.Multiply(OFFSET_VALUE)
    #     pt2_direction = DB.XYZ(-orientation.Y, orientation.X, 0)
    #     # offset = ref_direct.Multiply(OFFSET_VALUE)
    #     ref_array_1.Append(ref_dict.get('Left'))
    #     ref_array_1.Append(ref_dict.get('Right'))
    #     # test = DB.XYZ(orientation.Y, orientation.X, orientation.Z)
    #     dim_line_1 = DB.Line.CreateUnbound(family_instance.Location.Point.Add(offset), pt2_direction)
    #     dimension_1 = document.Create.NewDimension(document.ActiveView, dim_line_1, ref_array_1)
    # if ref_dict.get('Front') and ref_dict.get('Back'):
    #     OFFSET_VALUE = 2
    #     offset_direct = DB.XYZ(-orientation.Y, orientation.X, 0)
    #     offset = offset_direct.Multiply(-OFFSET_VALUE)
    #     ref_array_2.Append(ref_dict.get('Front'))
    #     ref_array_2.Append(ref_dict.get('Back'))
    #     test = DB.XYZ(orientation.Y, orientation.X, orientation.Z)
    #     dim_line_2 = DB.Line.CreateUnbound(family_instance.Location.Point.Add(offset), orientation)
    #     dimension_2 = document.Create.NewDimension(document.ActiveView, dim_line_2, ref_array_2)


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
    unassigned_instances = list(family_instances)
    instance_blocks = []
    instance_ids = [instance.Id.ToString() for instance in family_instances]

    for _id in instance_ids:
        current_instance = revit.doc.GetElement(DB.ElementId(int(_id)))
        bbox = current_instance.get_BoundingBox(revit.doc.ActiveView)
        outline = DB.Outline(bbox.Min, bbox.Max)
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
            # TODO Add top bottom dimensions to far left and right
            family_instances = [revit.doc.GetElement(DB.ElementId(int(_id))) for _id in block]
            if family_instances:
                create_dimension(revit.doc, family_instances)
