"""
This script creates interior elevations each room based on room boundary.
"""

#pylint: disable=import-error,invalid-name,broad-except
import clr
import math
# Import RevitAPI
clr.AddReference("RevitAPI")
import Autodesk
from Autodesk.Revit.DB import *

from pyrevit import revit
from pyrevit import script
from pyrevit import forms

__title__ = " Interior Elevations"
__author__ = "{{author}}"

# forms.inform_wip()

def checkCurves(curve1, curve2):
    v1 = curve1.Direction.Normalize()
    v2 = curve2.Direction.Normalize()
    if v1.IsAlmostEqualTo(v2):
        newLine = Line.CreateBound(curve2.GetEndPoint(0), curve1.GetEndPoint(1))
        return newLine
    else:
        return curve1

rooms, elems, names = [], [], []

col1 = FilteredElementCollector(revit.doc).OfCategory(BuiltInCategory.OST_Rooms).ToElements()

col2 = FilteredElementCollector(revit.doc).OfClass(ViewFamilyType).ToElements()


for v in col2:
    if Element.Name.GetValue(v) == "SSG_Interior Elevation":
        elems.append(v)

viewType = elems[0]

for room in col1:
    if room.Area != 0:
        rooms.append(room)
        # names.append(DB.Element.Name.GetValue(room))


res = forms.SelectFromList.show(rooms,
                                multiselect=True,
                                name_attr= 'Number',
                                button_name='Select Rooms')

bOptions = SpatialElementBoundaryOptions()


heights = []
curveLists = []
for r in res:
    heights.append(r.UnboundedHeight)
    boundSegs = r.GetBoundarySegments(bOptions)
    for bounds in boundSegs:
        curveLists.append(bounds)

            
output = []

for cList in curveLists:
    count = 0
    newCurves = []
    for c in cList:
        curve = c.GetCurve()

        if count == 0:
            newCurves.append(curve)
        else:
            newCurve = checkCurves(curve, newCurves[len(newCurves)-1])
            if newCurve == curve:
                newCurves.append(curve)
            else:
                newCurves[len(newCurves)-1] = newCurve
        count += 1

    if newCurves[0].Direction.Normalize().IsAlmostEqualTo(newCurves[len(newCurves)-1].Direction.Normalize()):
        newCurve = Line.ByStartPointEndPoint(newCurves[len(newCurves)-1].StartPoint, newCurves[0].EndPoint)
        newCurves.pop()
        newCurves[0] = newCurve

    output.append(newCurves)

    # print(len(newCurves))
    # print("-----")


# print(output)
# print("-----")

curves = []
old_curves = []
for out in output:

    # points = []
    # angles = []
    # curves = []
    for n in out:
        

        # print(str(n.GetEndPoint(0)) + " " + str(n.GetEndPoint(1)))
        rev = n.CreateReversed()
        # print(str(rev.GetEndPoint(0)) + " " + str(rev.GetEndPoint(1)))
        rev_dir = rev.Direction
        # print(rev_dir)
        zAxis = XYZ(0,0,1)
        cross = rev_dir.CrossProduct(zAxis)
        # print(cross)
        # print(rev)
        # print(rev_dir)

        # startPT = n.GetEndPoint(0)
        # endPT = n.GetEndPoint(1)
        # midPT = (startPT + endPT) / 2
        
        # midPT = n.Evaluate(n.Length/2, False)
        # cross = midPT.CrossProduct(rev_dir)
        # cross = midPT.CrossProduct(n.Direction)
        # newLine = n.CreateOffset(5, cross)
        newLine = n.CreateTransformed(Transform.CreateTranslation(5*cross))
        # newLineS = newLine.GetEndPoint(0)
        # newLineE = newLine.GetEndPoint(1)
        # newLineM = (newLineS + newLineE)/2
        # combY = newLineM.Y-midPT.Y
        # combX = newLineM.X-midPT.X
        # ang = math.atan2(combY, combX)
        # points.append(newLineM)
        # angles.append(ang)
        curves.append(newLine)
        old_curves.append(n)
        # print(newLine)
        # print("---")
        # print(str(newLine.GetEndPoint(0)) + " - " + str(newLine.GetEndPoint(1)))
# print(len(points))
# print(angles)

# print(curves)


views = []
with revit.Transaction("Create Elevations by Room"):
    for curve, old_curve in zip(curves, old_curves):
        startPT = curve.GetEndPoint(0)
        endPT = curve.GetEndPoint(1)
        midPT = (startPT + endPT)/2
        old_startPT = old_curve.GetEndPoint(0)
        old_endPT = old_curve.GetEndPoint(1)
        old_midPT = (old_startPT + old_endPT)/2
        combY = midPT.Y-old_midPT.Y
        combX = midPT.X-old_midPT.X
        ang = math.atan2(combY, combX)
        rotPT = XYZ(midPT.X, midPT.Y, midPT.Z + 1)
        ln = Line.CreateBound(midPT, rotPT)
        eleMarker = ElevationMarker.CreateElevationMarker(revit.doc, viewType.Id, midPT, 100)
        ele = eleMarker.CreateElevation(revit.doc, revit.doc.ActiveView.Id, 0)
        ElementTransformUtils.RotateElement(revit.doc, eleMarker.Id, ln, ang)
        wall_direct = old_curve.Direction
        print(wall_direct)
        view_direct = ele.ViewDirection
        print(view_direct)
        print(view_direct.AngleTo(wall_direct))
        print("---")

        # if math.degrees(ang) >= 170 and math.degrees(ang) <= 190:
        #     ElementTransformUtils.RotateElement(revit.doc, eleMarker.Id, ln, ang)
        views.append(ele)
        # print(math.degrees(ang))

        
'''
# for curveList, viewList, height in zip(curves, views, heights):
for height in heights:
    for curve, view in zip(curves,views):
        viewCropManager = view.GetCropRegionShapeManager()
        cLoop = viewCropManager.GetCropShape()[0]
        cLoopCurves = [x for x in cLoop]
        PointA = cLoopCurves[3].GetEndPoint(1)
        PointD = cLoopCurves[3].GetEndPoint(0)
        curveStart = curve.GetEndPoint(1)
        curveEnd = curve.GetEndPoint(0)
        curveMP = (curveStart + curveEnd)/2
        


        if curveMP.DistanceTo(curve.GetEndPoint(1)) < curveMP.DistanceTo(PointA):
            PointA = curve.GetEndPoint(1)		
            
        if curveMP.DistanceTo(curve.GetEndPoint(0)) < curveMP.DistanceTo(PointD):
            PointD = curve.GetEndPoint(0)			

        PointB = XYZ(PointA.X, PointA.Y, PointA.Z + height)
        PointC = XYZ(PointD.X, PointD.Y, PointD.Z + height)

        print(PointA)
        print(PointB)
        print(PointC)
        print(PointD)
        print("---")

        # try:
        LineA = Line.CreateBound(PointA,PointB)
        LineB = Line.CreateBound(PointB,PointC)
        LineC = Line.CreateBound(PointC,PointD)
        LineD = Line.CreateBound(PointD,PointA)
        #     curveLoop = CurveLoop.Create([LineA, LineB, LineC, LineD])

        #     with revit.Transaction("Crop Elevations"):		
        #         viewCropManager.SetCropShape(curveLoop)
        # except:
        #     print("Problem creating lines")
'''