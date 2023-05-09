import math

from pyrevit import revit, DB, script, forms
from rooms import select_placed_rooms, get_number, get_name
from Autodesk.Revit import Exceptions



def check_combined_curves(curve1, curve2):
    v1 = curve1.Direction.Normalize()
    v2 = curve2.Direction.Normalize()
    if v1.IsAlmostEqualTo(v2):
        return DB.Line.CreateBound(curve2.GetEndPoint(0), curve1.GetEndPoint(1))
    else:
        return curve1
    
def get_curves_from_boundary(boundary_segments):
    potential_curves, curve_list = [], []
    for segment_list in boundary_segments:
        for i, segment in enumerate(segment_list):
            segment_curve = segment.GetCurve()
            
            # add first curve
            if i == 0:
                potential_curves.append(segment_curve)
                
            # check if next curves should be combined
            else:
                new_curve = check_combined_curves(
                    segment_curve, potential_curves[len(potential_curves) - 1]
                )
                if new_curve == segment_curve:
                    potential_curves.append(segment_curve)
                # replace previous curve with combined curve
                else:
                    potential_curves[len(potential_curves) - 1] = new_curve
    for curve in potential_curves:
        if curve.Length >= OFFSET:
            curve_list.append(curve)
        
    return curve_list


def isclose(a, b, rel_tol=1e-09, abs_tol=0.0):
    return abs(a - b) <= max(rel_tol * max(abs(a), abs(b)), abs_tol)


def get_direction(degrees):
    if 337.5 <= degrees <= 360 or 0 <= degrees < 22.5:
        return 'West'
    elif 22.5 <= degrees < 67.5:
        return 'Northwest'
    elif 67.5 <= degrees < 112.5:
        return 'North'
    elif 112.5 <= degrees < 157.5:
        return 'Northeast'
    elif 157.5 <= degrees < 202.5:
        return 'East'
    elif 202.5 <= degrees < 247.5:
        return 'Southeast'
    elif 247.5 <= degrees < 292.5:
        return 'South'
    elif 292.5 <= degrees < 337.5:
        return 'Southwest'
    else:
        return 'Invalid degrees value'
    
def get_unique_elevation_name(degrees, current_view_names):
    direction_name = get_direction(degrees)
    elevation_name = "Elevation - {} - {} - {}".format(get_number(room), get_name(room), direction_name)

    # Check if the elevation name already exists
    count = 1
    while elevation_name in current_view_names:
        elevation_name = " {} ({})".format(elevation_name, count)
        count += 1

    return elevation_name

OFFSET = 7.0

elevation_type_id = revit.doc.GetDefaultElementTypeId(
    DB.ElementTypeGroup.ViewTypeElevation
)

view_names = []
elevation_views = DB.FilteredElementCollector(revit.doc).OfClass(DB.ViewSection).ToElements()
for view in elevation_views:
    if view.IsTemplate == False:
        view_names.append(view.Name)


rooms = select_placed_rooms(revit.doc, active_view_only=True)


if rooms:


    max_value = len(rooms)
    boundary_options = DB.SpatialElementBoundaryOptions()
    
    for room in rooms:

        height = room.UnboundedHeight
        boundary_segments = room.GetBoundarySegments(boundary_options)
        curve_list = get_curves_from_boundary(boundary_segments)
  

        if (
            curve_list[0]
            .Direction.Normalize()
            .IsAlmostEqualTo(
                curve_list[len(curve_list) - 1].Direction.Normalize()
            )
        ):
            start_point = curve_list[len(curve_list) - 1].StartPoint
            end_point = curve_list[0].EndPoint
            new_curve = DB.Line.ByStartPointEndPoint(start_point, end_point)
            curve_list.pop()
            curve_list[0] = new_curve

        max_value = len(curve_list)
        with revit.Transaction("Create boundary elevations"):
            with forms.ProgressBar() as pb:
                for count, segment_curve in enumerate(curve_list):
                    reversed_segment = segment_curve.CreateReversed()
                    reversed_direction = reversed_segment.Direction
                    z_axis = DB.XYZ(0, 0, 1)
                    reversed_cross_product = reversed_direction.CrossProduct(z_axis)

                    new_line = segment_curve.CreateTransformed(
                        DB.Transform.CreateTranslation(6 * reversed_cross_product)
                    )

                    start_pt = new_line.GetEndPoint(0)
                    end_pt = new_line.GetEndPoint(1)

                    num1 = (start_pt.X + end_pt.X) / 2
                    num2 = (start_pt.Y + end_pt.Y) / 2
                    num3 = (start_pt.Z + end_pt.Z) / 2

                    xyz1 = DB.XYZ(start_pt.X, start_pt.Y, start_pt.Z + 5.0) - start_pt
                    xyz2 = (end_pt - start_pt).CrossProduct(xyz1)

                    num4 = DB.XYZ.BasisY.AngleTo(xyz2)

                    xyz3 = DB.XYZ(num1, num2, num3)

                    bound = DB.Line.CreateBound(xyz3, DB.XYZ(num1, num2, num3 + 5.0))

                    xyz4 = xyz2.Negate()
                    xyz2.Normalize()

                    xyz5 = xyz4.Normalize()




                    elevation_marker = DB.ElevationMarker.CreateElevationMarker(
                        revit.doc, elevation_type_id, xyz3, 100
                    )
                    elevation = elevation_marker.CreateElevation(
                        revit.doc, revit.doc.ActiveView.Id, 1
                    )
                    DB.ElementTransformUtils.RotateElement(
                        revit.doc, elevation_marker.Id, bound, num4
                    )
                    xyz6 = elevation.ViewDirection.Normalize()
                    num5 = xyz5.DotProduct(xyz6)

                    if isclose(num5, -1.0):
                        view_section = elevation_marker.CreateElevation(
                            revit.doc, revit.doc.ActiveView.Id, 3
                        )
                        revit.doc.Delete(elevation.Id)

                    elif isclose(num5, 1.0):
                        # if int(num5) == 1:
                        elevation2 = elevation_marker.CreateElevation(
                            revit.doc, revit.doc.ActiveView.Id, 2
                        )
                        revit.doc.Delete(elevation.Id)
                        view_section = elevation_marker.CreateElevation(
                            revit.doc, revit.doc.ActiveView.Id, 1
                        )
                        revit.doc.Delete(elevation2.Id)
                            # views.append(viewSection)
                            # print("section2")

                    else:
                        DB.ElementTransformUtils.RotateElement(
                            revit.doc, elevation_marker.Id, bound, -(2.0 * num4)
                        )
                        elevation3 = elevation_marker.CreateElevation(
                            revit.doc, revit.doc.ActiveView.Id, 2
                        )
                        revit.doc.Delete(elevation.Id)
                        view_section = elevation_marker.CreateElevation(
                            revit.doc, revit.doc.ActiveView.Id, 1
                        )
                        revit.doc.Delete(elevation3.Id)


                        if int(num5) == -1:

                            elevation4 = elevation_marker.CreateElevation(
                                revit.doc, revit.doc.ActiveView.Id, 3
                            )
                            revit.doc.Delete(view_section.Id)
                            view_section = elevation4


                    far_clip_param = view_section.get_Parameter(
                        DB.BuiltInParameter.VIEWER_BOUND_OFFSET_FAR
                    )
                    far_clip_param.SetValueString("str(OFFSET)'")
                    direct = view_section.ViewDirection
                    angle = direct.AngleOnPlaneTo(DB.XYZ.BasisX, DB.XYZ.BasisZ)
                    
                    new_name = get_unique_elevation_name(math.degrees(angle), view_names)
                    revit.update.set_name(view_section, new_name)
                    view_names.append(new_name)

                    view_crop_manager = view_section.GetCropRegionShapeManager()
                    curve_loop = view_crop_manager.GetCropShape()[0]
                    curve_loop_curves = [x for x in curve_loop]
                    pt_a = curve_loop_curves[3].GetEndPoint(1)
                    pt_d = curve_loop_curves[3].GetEndPoint(0)
                    curve_start = segment_curve.GetEndPoint(1)
                    curve_end = segment_curve.GetEndPoint(0)
                    curve_mid = (curve_start + curve_end) / 2

                    if curve_mid.DistanceTo(
                        segment_curve.GetEndPoint(1)
                    ) < curve_mid.DistanceTo(pt_a):
                        pt_a = segment_curve.GetEndPoint(1)

                    if curve_mid.DistanceTo(
                        segment_curve.GetEndPoint(0)
                    ) < curve_mid.DistanceTo(pt_d):
                        pt_d = segment_curve.GetEndPoint(0)

                    pt_b = DB.XYZ(pt_a.X, pt_a.Y, pt_a.Z + height)
                    pt_c = DB.XYZ(pt_d.X, pt_d.Y, pt_d.Z + height)

                    line_a = DB.Line.CreateBound(pt_a, pt_b)
                    line_b = DB.Line.CreateBound(pt_b, pt_c)
                    line_c = DB.Line.CreateBound(pt_c, pt_d)
                    line_d = DB.Line.CreateBound(pt_d, pt_a)

                    new_curve_loop = DB.CurveLoop.Create(
                        [line_a, line_b, line_c, line_d]
                    )

                    try:
                        view_crop_manager.SetCropShape(new_curve_loop)
                    except Exceptions.ArgumentException:
                        print("Unable to modify crop region")
                        
                    pb.update_progress(count, max_value)