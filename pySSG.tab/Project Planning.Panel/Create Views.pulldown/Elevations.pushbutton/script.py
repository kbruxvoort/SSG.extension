# pylint: disable=import-error,invalid-name,broad-except
import clr
import math

# Import RevitAPI
clr.AddReference("RevitAPI")
import Autodesk
from Autodesk.Revit.DB import *
from Autodesk.Revit.Exceptions import ArgumentException

from pyrevit import revit
from pyrevit import script
from pyrevit import forms


# forms.check_viewtype(revit.doc.ActiveView, ViewType.FloorPlan, exitscript=True)

logger = script.get_logger()
output = script.get_output()


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
        newLine = Line.CreateBound(curve2.GetEndPoint(0), curve1.GetEndPoint(1))
        return newLine
    else:
        return curve1


def isclose(a, b, rel_tol=1e-09, abs_tol=0.0):
    return abs(a - b) <= max(rel_tol * max(abs(a), abs(b)), abs_tol)


rooms, elems, names = [], [], []

col1 = (
    FilteredElementCollector(revit.doc)
    .OfCategory(BuiltInCategory.OST_Rooms)
    .ToElements()
)

col2 = FilteredElementCollector(revit.doc).OfClass(ViewFamilyType).ToElements()


for v in col2:
    if "Interior Elevation" in Element.Name.GetValue(v):
        elems.append(v)

viewType = elems[0]

for room in col1:
    if room.Area != 0:
        rooms.append(room)


res = forms.SelectFromList.show(
    sorted([RoomOption(x) for x in rooms], key=lambda x: x.Number),
    multiselect=True,
    # name_attr= 'Number',
    button_name="Select Rooms",
)


heights = []
curveLists = []
names = []

bOptions = SpatialElementBoundaryOptions()
if res:
    for r in res:
        heights.append(r.UnboundedHeight)
        boundSegs = r.GetBoundarySegments(bOptions)

        for bounds in boundSegs:
            curveLists.append(bounds)

out_list = []
for cList in curveLists:
    count = 0
    newCurves = []
    for c in cList:
        curve = c.GetCurve()

        if count == 0:
            newCurves.append(curve)
        else:
            newCurve = checkCurves(curve, newCurves[len(newCurves) - 1])
            if newCurve == curve:
                newCurves.append(curve)
            else:
                newCurves[len(newCurves) - 1] = newCurve
        count += 1

    if (
        newCurves[0]
        .Direction.Normalize()
        .IsAlmostEqualTo(newCurves[len(newCurves) - 1].Direction.Normalize())
    ):
        newCurve = Line.ByStartPointEndPoint(
            newCurves[len(newCurves) - 1].StartPoint, newCurves[0].EndPoint
        )
        newCurves.pop()
        newCurves[0] = newCurve

    out_list.append(newCurves)


curves = []
old_curves = []
for out in out_list:
    for n in out:
        rev = n.CreateReversed()

        rev_dir = rev.Direction

        zAxis = XYZ(0, 0, 1)
        cross = rev_dir.CrossProduct(zAxis)

        newLine = n.CreateTransformed(Transform.CreateTranslation(6 * cross))

        curves.append(newLine)
        old_curves.append(n)


views = []

for curve in curves:
    startPT = curve.GetEndPoint(0)
    endPT = curve.GetEndPoint(1)

    num1 = (startPT.X + endPT.X) / 2
    num2 = (startPT.Y + endPT.Y) / 2
    num3 = (startPT.Z + endPT.Z) / 2

    xyz1 = XYZ(startPT.X, startPT.Y, startPT.Z + 5.0) - startPT
    xyz2 = (endPT - startPT).CrossProduct(xyz1)

    num4 = XYZ.BasisY.AngleTo(xyz2)

    xyz3 = XYZ(num1, num2, num3)

    bound = Line.CreateBound(xyz3, XYZ(num1, num2, num3 + 5.0))

    xyz4 = xyz2.Negate()
    xyz2.Normalize()

    xyz5 = xyz4.Normalize()

    try:

        with revit.Transaction("Create Elevations by Room"):
            eleMarker = ElevationMarker.CreateElevationMarker(
                revit.doc, viewType.Id, xyz3, 100
            )
            ele1 = eleMarker.CreateElevation(revit.doc, revit.doc.ActiveView.Id, 1)
            ElementTransformUtils.RotateElement(revit.doc, eleMarker.Id, bound, num4)
            xyz6 = ele1.ViewDirection.Normalize()
            num5 = xyz5.DotProduct(xyz6)
            # print(num5)
            # print(type(num5))

            if isclose(num5, -1.0):
                viewSection = eleMarker.CreateElevation(
                    revit.doc, revit.doc.ActiveView.Id, 3
                )
                revit.doc.Delete(ele1.Id)
                views.append(viewSection)
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
                    views.append(viewSection)
                    # print("section2")

            else:
                ElementTransformUtils.RotateElement(
                    revit.doc, eleMarker.Id, bound, -(2.0 * num4)
                )
                ele3 = eleMarker.CreateElevation(revit.doc, revit.doc.ActiveView.Id, 2)
                revit.doc.Delete(ele1.Id)
                viewSection = eleMarker.CreateElevation(
                    revit.doc, revit.doc.ActiveView.Id, 1
                )
                revit.doc.Delete(ele3.Id)
                # print("section3")

                try:
                    num5 = xyz5.DotProduct(viewSection.ViewDirection.Normalize())
                    # print(num5)

                except:
                    pass

                if int(num5) == -1:
                    # print("-1")
                    # print("---")
                    ele4 = eleMarker.CreateElevation(
                        revit.doc, revit.doc.ActiveView.Id, 3
                    )
                    revit.doc.Delete(viewSection.Id)
                    views.append(ele4)
                else:
                    views.append(viewSection)
                    # print("-----")

    except:
        print("error")


# print(len(views))
total_work = len(views)
with revit.Transaction("Rename Elevation"):
    for idx, view in enumerate(views):
        farClip = view.get_Parameter(BuiltInParameter.VIEWER_BOUND_OFFSET_FAR)
        farClip.SetValueString("6.25'")
        filt = ElementCategoryFilter(BuiltInCategory.OST_Rooms)
        collect = FilteredElementCollector(
            revit.doc, view.Id
        ).WhereElementIsNotElementType()
        collect = collect.WherePasses(filt)
        room = collect.FirstElement()

        roomName = room.LookupParameter("Name").AsString().upper()
        roomNumber = room.LookupParameter("Number").AsString()

        direct = view.ViewDirection
        angle = direct.AngleOnPlaneTo(XYZ.BasisX, XYZ.BasisZ)
        degrees = round(math.degrees(angle) / 45) * 45
        # print(str(math.degrees(angle)) + " > " + str(degrees))

        if degrees == 45:
            direction = "NORTHWEST"
        elif degrees == 90:
            direction = "NORTH"
        elif degrees == 135:
            direction = "NORTHEAST"
        elif degrees == 180:
            direction = "EAST"
        elif degrees == 225:
            direction = "SOUTHEAST"
        elif degrees == 270:
            direction = "SOUTH"
        elif degrees == 315:
            direction = "SOUTHWEST"
        else:
            direction = "WEST"
        # print(degrees)
        # print(direction)

        newName = "ELEVATION - " + roomName + " " + roomNumber + " - " + direction
        # print(newName)

        try:
            print('Creating Elevation "%s"' % newName)
            view.ViewName = newName
        except ArgumentException:
            try:
                message = 'View Name "%s" already exists. Adding Copy to Name' % newName
                logger.warning(message)
                view.ViewName = newName + " (Copy)"
            except ArgumentException:
                message = 'View Name "%s" already exists. Unable to Rename' % newName
                logger.error(message)

        # print(newName)
        output.update_progress(idx + 1, total_work)

# for curveList, viewList, height in zip(curves, views, heights):
# for height in heights:
for curve, view in zip(curves, views):
    # print(view.ViewName)
    height = heights[0]
    viewCropManager = view.GetCropRegionShapeManager()
    cLoop = viewCropManager.GetCropShape()[0]
    cLoopCurves = [x for x in cLoop]
    PointA = cLoopCurves[3].GetEndPoint(1)
    PointD = cLoopCurves[3].GetEndPoint(0)
    curveStart = curve.GetEndPoint(1)
    curveEnd = curve.GetEndPoint(0)
    curveMP = (curveStart + curveEnd) / 2

    if curveMP.DistanceTo(curve.GetEndPoint(1)) < curveMP.DistanceTo(PointA):
        PointA = curve.GetEndPoint(1)

    if curveMP.DistanceTo(curve.GetEndPoint(0)) < curveMP.DistanceTo(PointD):
        PointD = curve.GetEndPoint(0)

    PointB = XYZ(PointA.X, PointA.Y, PointA.Z + height)
    PointC = XYZ(PointD.X, PointD.Y, PointD.Z + height)

    LineA = Line.CreateBound(PointA, PointB)
    LineB = Line.CreateBound(PointB, PointC)
    LineC = Line.CreateBound(PointC, PointD)
    LineD = Line.CreateBound(PointD, PointA)

    curveLoop = CurveLoop.Create([LineA, LineB, LineC, LineD])
    # print(PointA)
    # print(PointB)
    # print(PointC)
    # print(PointD)

    with revit.Transaction("Crop Elevations"):
        try:
            viewCropManager.SetCropShape(curveLoop)
        except:
            print("Unable to modify crop region")

print("Completed\n")