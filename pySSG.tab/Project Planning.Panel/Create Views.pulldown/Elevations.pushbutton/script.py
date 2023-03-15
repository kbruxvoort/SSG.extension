# pylint: disable=import-error,invalid-name,broad-except
import math

from pyrevit import revit, DB
from pyrevit import script
from pyrevit import forms

from Autodesk.Revit import Exceptions


class RoomOption(forms.TemplateListItem):
    # def __init__(self, room_element):
    #     super(RoomOption, self).__init__(room_element)

    @property
    def name(self):
        """Room name."""
        return "%s" % revit.query.get_name(self.item)


def checkCurves(curve1, curve2):
    v1 = curve1.Direction.Normalize()
    v2 = curve2.Direction.Normalize()
    if v1.IsAlmostEqualTo(v2):
        return DB.Line.CreateBound(curve2.GetEndPoint(0), curve1.GetEndPoint(1))
    else:
        return curve1


def isclose(a, b, rel_tol=1e-09, abs_tol=0.0):
    return abs(a - b) <= max(rel_tol * max(abs(a), abs(b)), abs_tol)


logger = script.get_logger()
output = script.get_output()

OFFSET = 6.25


# rooms, elems, names = [], [], []

categories = [DB.BuiltInCategory.OST_Rooms]
rooms = [x for x in revit.query.get_elements_by_categories(categories) if x.Area > 0]

if rooms:

    type_name = "Interior Elevation"
    view_types = [
        x
        for x in revit.query.get_types_by_class(DB.ViewFamilyType)
        if revit.query.get_name(x) == type_name
    ]
    if not view_types:
        view_types = [revit.doc.GetElement(revit.doc.GetDefaultElementTypeId(DB.ElementTypeGroup.ViewTypeElevation))]
    view_names = [
        revit.query.get_name(x) for x in revit.query.get_elements_by_class(DB.View)
    ]
    # print(view_names)

    if view_types:

        selected = forms.SelectFromList.show(
            sorted([RoomOption(x) for x in rooms], key=lambda x: x.Number),
            multiselect=True,
            # name_attr= 'Number',
            button_name="Select Rooms",
        )

        if selected:
            total_work = len(selected)

            # heights = []
            # curveLists = []
            # names = []
            # out_list = []

            # room_data = {}

            bOptions = DB.SpatialElementBoundaryOptions()
            # if rooms:
            for r in selected:

                # room_data['height'] = r.UnboundedHeight
                height = r.UnboundedHeight
                bound_segs = r.GetBoundarySegments(bOptions)
                room_name = r.get_Parameter(DB.BuiltInParameter.ROOM_NAME).AsString()
                room_number = r.get_Parameter(
                    DB.BuiltInParameter.ROOM_NUMBER
                ).AsString()

                for segment_list in bound_segs:
                    count = 0
                    new_curves = []
                    for segment in segment_list:
                        curve = segment.GetCurve()
                        if count == 0:
                            new_curves.append(curve)
                        else:
                            new_curve = checkCurves(
                                curve, new_curves[len(new_curves) - 1]
                            )
                            if new_curve == curve:
                                new_curves.append(curve)
                            else:
                                new_curves[len(new_curves) - 1] = new_curve
                        count += 1

                if (
                    new_curves[0]
                    .Direction.Normalize()
                    .IsAlmostEqualTo(
                        new_curves[len(new_curves) - 1].Direction.Normalize()
                    )
                ):
                    start_point = new_curves[len(new_curves) - 1].StartPoint
                    end_point = new_curves[0].EndPoint
                    new_curve = DB.Line.ByStartPointEndPoint(start_point, end_point)
                    new_curves.pop()
                    new_curves[0] = new_curve

                total_work = len(new_curves)
                prog = 0
                for curve in new_curves:
                    rev = curve.CreateReversed()
                    rev_dir = rev.Direction
                    z_axis = DB.XYZ(0, 0, 1)
                    cross = rev_dir.CrossProduct(z_axis)

                    new_line = curve.CreateTransformed(
                        DB.Transform.CreateTranslation(6 * cross)
                    )

                    startPT = new_line.GetEndPoint(0)
                    endPT = new_line.GetEndPoint(1)

                    num1 = (startPT.X + endPT.X) / 2
                    num2 = (startPT.Y + endPT.Y) / 2
                    num3 = (startPT.Z + endPT.Z) / 2

                    xyz1 = DB.XYZ(startPT.X, startPT.Y, startPT.Z + 5.0) - startPT
                    xyz2 = (endPT - startPT).CrossProduct(xyz1)

                    num4 = DB.XYZ.BasisY.AngleTo(xyz2)

                    xyz3 = DB.XYZ(num1, num2, num3)

                    bound = DB.Line.CreateBound(xyz3, DB.XYZ(num1, num2, num3 + 5.0))

                    xyz4 = xyz2.Negate()
                    xyz2.Normalize()

                    xyz5 = xyz4.Normalize()

                    try:

                        with revit.Transaction("Create Elevations by Room"):
                            eleMarker = DB.ElevationMarker.CreateElevationMarker(
                                revit.doc, view_types[0].Id, xyz3, 100
                            )
                            ele1 = eleMarker.CreateElevation(
                                revit.doc, revit.doc.ActiveView.Id, 1
                            )
                            DB.ElementTransformUtils.RotateElement(
                                revit.doc, eleMarker.Id, bound, num4
                            )
                            xyz6 = ele1.ViewDirection.Normalize()
                            num5 = xyz5.DotProduct(xyz6)

                            if isclose(num5, -1.0):
                                viewSection = eleMarker.CreateElevation(
                                    revit.doc, revit.doc.ActiveView.Id, 3
                                )
                                revit.doc.Delete(ele1.Id)
                                # views.append(viewSection)
                                # print("section1")

                            elif isclose(num5, 1.0):
                                if int(num5) == 1:
                                    ele2 = eleMarker.CreateElevation(
                                        revit.doc, revit.doc.ActiveView.Id, 2
                                    )
                                    revit.doc.Delete(ele1.Id)
                                    viewSection = eleMarker.CreateElevation(
                                        revit.doc, revit.doc.ActiveView.Id, 1
                                    )
                                    revit.doc.Delete(ele2.Id)
                                    # views.append(viewSection)
                                    # print("section2")

                            else:
                                DB.ElementTransformUtils.RotateElement(
                                    revit.doc, eleMarker.Id, bound, -(2.0 * num4)
                                )
                                ele3 = eleMarker.CreateElevation(
                                    revit.doc, revit.doc.ActiveView.Id, 2
                                )
                                revit.doc.Delete(ele1.Id)
                                viewSection = eleMarker.CreateElevation(
                                    revit.doc, revit.doc.ActiveView.Id, 1
                                )
                                revit.doc.Delete(ele3.Id)

                                try:
                                    num5 = xyz5.DotProduct(
                                        viewSection.ViewDirection.Normalize()
                                    )

                                except:
                                    pass

                                if int(num5) == -1:
                                    print("-1")
                                    # print("---")
                                    ele4 = eleMarker.CreateElevation(
                                        revit.doc, revit.doc.ActiveView.Id, 3
                                    )
                                    revit.doc.Delete(viewSection.Id)
                                    # views.append(ele4)
                                    viewSection = ele4
                                else:
                                    # views.append(viewSection)
                                    pass
                                    # print("-----")

                            farClip = viewSection.get_Parameter(
                                DB.BuiltInParameter.VIEWER_BOUND_OFFSET_FAR
                            )
                            farClip.SetValueString("str(OFFSET)'")
                            direct = viewSection.ViewDirection
                            angle = direct.AngleOnPlaneTo(DB.XYZ.BasisX, DB.XYZ.BasisZ)
                            degrees = round(math.degrees(angle) / 45) * 45
                            # print(str(math.degrees(angle)) + " > " + str(degrees))

                            if degrees == 45:
                                direction = "Northwest"
                            elif degrees == 90:
                                direction = "North"
                            elif degrees == 135:
                                direction = "Northeast"
                            elif degrees == 180:
                                direction = "East"
                            elif degrees == 225:
                                direction = "Southeast"
                            elif degrees == 270:
                                direction = "South"
                            elif degrees == 315:
                                direction = "Southwest"
                            else:
                                direction = "West"
                            # print(degrees)
                            # print(direction)

                            new_name = (
                                "Elevation - "
                                + room_name
                                + " "
                                + room_number
                                + " - "
                                + direction
                            )
                            # print(new_name)

                            try:
                                # print('Creating Elevation "%s"' % new_name)
                                revit.update.set_name(viewSection, new_name)
                                message = 'Successfully created "{}"'.format(new_name)
                                logger.success(message)
                                view_names.append(new_name)
                            except Exceptions.ArgumentException:

                                count = 1
                                copy_name = new_name + "(" + str(count) + ")"
                                while copy_name in view_names:
                                    count += 1
                                    copy_name = new_name + "(" + str(count) + ")"
                                message = 'View Name "{}" already exists. Appending ({}) to name'.format(
                                    new_name, str(count)
                                )
                                logger.warning(message)
                                revit.update.set_name(viewSection, copy_name)
                                view_names.append(copy_name)

                            viewCropManager = viewSection.GetCropRegionShapeManager()
                            cLoop = viewCropManager.GetCropShape()[0]
                            cLoopCurves = [x for x in cLoop]
                            PointA = cLoopCurves[3].GetEndPoint(1)
                            PointD = cLoopCurves[3].GetEndPoint(0)
                            curveStart = curve.GetEndPoint(1)
                            curveEnd = curve.GetEndPoint(0)
                            curveMP = (curveStart + curveEnd) / 2

                            if curveMP.DistanceTo(
                                curve.GetEndPoint(1)
                            ) < curveMP.DistanceTo(PointA):
                                PointA = curve.GetEndPoint(1)

                            if curveMP.DistanceTo(
                                curve.GetEndPoint(0)
                            ) < curveMP.DistanceTo(PointD):
                                PointD = curve.GetEndPoint(0)

                            PointB = DB.XYZ(PointA.X, PointA.Y, PointA.Z + height)
                            PointC = DB.XYZ(PointD.X, PointD.Y, PointD.Z + height)

                            LineA = DB.Line.CreateBound(PointA, PointB)
                            LineB = DB.Line.CreateBound(PointB, PointC)
                            LineC = DB.Line.CreateBound(PointC, PointD)
                            LineD = DB.Line.CreateBound(PointD, PointA)

                            curveLoop = DB.CurveLoop.Create(
                                [LineA, LineB, LineC, LineD]
                            )

                            try:
                                viewCropManager.SetCropShape(curveLoop)
                            except Exceptions.ArgumentException:
                                print("Unable to modify crop region")

                            prog += 1

                            output.update_progress(prog, total_work)

                    except:
                        print("error")
            print("Completed")
