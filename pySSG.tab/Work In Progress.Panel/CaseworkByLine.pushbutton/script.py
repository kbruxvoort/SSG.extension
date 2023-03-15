import clr
import os
import math
import itertools

# from System import EventHandler, Uri
from System.Collections.Generic import List
from pyrevit import HOST_APP
from pyrevit import revit, DB, UI
from pyrevit import script
from pyrevit import forms

__title__ = "Casework\nBy Line"
__author__ = "{{author}}"

class FamilyLoadOptions(DB.IFamilyLoadOptions):
    'A Class implementation for loading families'

    def OnFamilyFound(self, familyInUse, overwriteParameterValues):
        'Defines behavior when a family is found in the model.'
        overwriteParameterValues = True
        return True

    def OnSharedFamilyFound(self, sharedFamily, familyInUse, source, overwriteParameterValues):
        'Defines behavior when a shared family is found in the model.'
        source = DB.FamilySource.Project
        # source = FamilySource.Family
        overwriteParameterValues = True
        return True

def load_family(folder_path='D:\\Desktop', file_name='Insert File Name Here'):
    'Loads a family into the Revit project with path and file name.'
    family_path = os.path.join(folder_path, file_name)
    if os.path.exists(family_path) is False:
        return 'Path does not exist.'

    family_loaded = clr.Reference[DB.Family]()
    
    with revit.Transaction('Load Family'):

        loaded = revit.doc.LoadFamily(family_path, FamilyLoadOptions(), family_loaded)
        if loaded:
            family = family_loaded.Value
            symbols = []

            for family_symbol_id in family.GetFamilySymbolIds():
                family_symbol = revit.doc.GetElement(family_symbol_id)
                symbols.append(family_symbol)

            for s in symbols:
                try:
                    s.Activate()
                except:
                    pass

            # t.Commit()
            return symbols

        else:
            # t.Commit()
            return 'Family already exists in project.'

def get_intersection(line1, line2):
    results = clr.Reference[DB.IntersectionResultArray]()
    # See ironpython.net/documentation/dotnet for clr.Reference
    result = line1.Intersect(line2, results)
    # http://www.revitapidocs.com/2018/51961478-fb36-e00b-2d1b-7db27b0a09e6.htm
    if result == DB.SetComparisonResult.Overlap:
        intersection = results.Item[0]
        # angle = line1.GetEndPoint(1).AngleTo(line2.GetEndPoint(0))
        # print(math.degrees(line1.GetEndPoint(1).AngleTo(line2.GetEndPoint(1))))
        return intersection.XYZPoint

# def compare_vectors(vector, vector_list):
#     x = False
#     for v in vector_list:
#         if v.IsAlmostEqualTo(vector):
#             x = True
#             break
#     return x
    
# def angle_between_vectors(v1, v2):
#     a1 = math.atan2(v1.Y, v1.X)
#     a2 = math.atan2(v2.Y, v2.X)
#     angle = a2 - a1
#     # print(math.degrees(a1), math.degrees(a2), math.degrees(angle))
#     # print(math.degrees(v1.AngleTo(v2)))
#     if angle < 0:
#         angle += 2 * math.pi
#     return angle

# def ccw_angle(v1, v2):
#     return math.atan2(v1.X * v2.Y - v1.Y * v2.X, v1.X * v2.X + v1.Y * v2.Y) % (math.pi * 2)

def find_centroid(curve_list):
    vector_list = []
    for c in curve_list:
        ele = revit.doc.GetElement(c)
        line = ele.Location.Curve
        p, q = line.GetEndPoint(0), line.GetEndPoint(1)
        vector_list.append(p)
        vector_list.append(q)
    x = 0
    y = 0
    total = len(vector_list)
    for v in vector_list:
        x += v.X
        y += v.Y
    center = (DB.XYZ(x/total, y/total, 0))
    return center

# def dotproduct(v1, v2):
#   return sum((a*b) for a, b in zip(v1, v2))

def getAngle(a, b, c):
    dir_CA = math.atan2(a.Y-c.Y, a.X-c.X)
    dir_CB = math.atan2(b.Y-c.Y, b.X-c.X)
    angle = dir_CA - dir_CB
    if angle > math.pi:
        angle -= 2 * math.pi
    elif angle < - math.pi:
        angle += 2 * math.pi
    return angle

# def getAngle2(v1, v2):
#     angle = math.atan2(v2.Y, v2.X) - math.atan2(v1.Y, v1.X)
#     if angle < 0:
#         angle += 2 * math.pi
#     return angle

# def length(v):
#   return math.sqrt(v.DotProduct(v))

# def internal_angle(v1, v2):
#   return math.acos(v1.DotProduct(v2) / (length(v1) * length(v2)))

def OnDocumentChanged(sender, e):
    listId.AddRange(e.GetAddedElementIds())


output = script.get_output()
logger = script.get_logger()

std_sizes = [3.5, 3, 2.5, 2, 1.5, 1.25, 1]
depth = 2

plan_view = revit.doc.ActiveView 
forms.check_viewtype(plan_view, DB.ViewType.FloorPlan, exitscript=True)
viewTypeId = plan_view.GetTypeId()

gen_fams = DB.FilteredElementCollector(revit.doc).\
                                                OfCategory(DB.BuiltInCategory.OST_GenericModel).\
                                                OfClass(DB.FamilySymbol)
if gen_fams:
    line_fam = [x for x in gen_fams if x.FamilyName == "SSG_Placement_Line"][0]

case_fams = DB.FilteredElementCollector(revit.doc).\
                                                OfCategory(DB.BuiltInCategory.OST_Casework).\
                                                OfClass(DB.FamilySymbol)
if case_fams:
    corner_filler = [x for x in case_fams if x.FamilyName == "SSG_Filler_Base_Corner_LAM"][0]


listId = List[DB.ElementId]()
opt = UI.PromptForFamilyInstancePlacementOptions()
# opt.FaceBasedPlacementType.PlaceOnWorkPlane
opt.FaceBasedPlacementType.PlaceOnWorkPlane

revit.events.add_handler('doc-changed', OnDocumentChanged)
revit.uidoc.PromptForFamilyInstancePlacement(line_fam, opt)
# revit.uidoc.PostRequestForElementTypePlacement(line_fam)
revit.events.remove_handler('doc-changed', OnDocumentChanged)
'''
lines = list(listId)
count = len(listId)
v_list = []
if count > 1:
    with revit.Transaction('Line Test'):
        # center = find_centroid(lines)
        for i in range(count):

            prev_ele = revit.doc.GetElement(lines[i-1])
            curr_ele = revit.doc.GetElement(lines[i])

            prev_line = prev_ele.Location.Curve
            curr_line = curr_ele.Location.Curve

            prev_sP = prev_line.GetEndPoint(0)
            prev_eP = prev_line.GetEndPoint(1)

            curr_sP = curr_line.GetEndPoint(0)
            curr_eP = curr_line.GetEndPoint(1)

            curr_V = curr_eP - curr_sP
            prev_V = prev_eP - prev_sP

            direction = curr_line.Direction
            new_sP = curr_sP
            new_eP = curr_eP
            
            if curr_sP.IsAlmostEqualTo(prev_eP):
                angle = getAngle(curr_eP, prev_sP, curr_sP)
                gap = depth * math.tan(math.radians(90) - abs(angle)/2) + .333333333333
                new_sP = curr_sP + gap * direction
                axis = DB.Line.CreateBound(curr_sP, curr_sP.Add(DB.XYZ(0,0,1)))
                angleX = direction.AngleTo(DB.XYZ.BasisX)
                # print(math.degrees(angleX))
                filler = revit.doc.Create.NewFamilyInstance(curr_sP, corner_filler, DB.Structure.StructuralType.NonStructural)
                DB.ElementTransformUtils.RotateElement(revit.doc, filler.Id, axis, .75 * math.pi + angleX - angle/2)


            if i != count - 1:
                next_ele = revit.doc.GetElement(lines[i+1])
                next_line = next_ele.Location.Curve
                next_sP = next_line.GetEndPoint(0)
                next_eP = next_line.GetEndPoint(1)
                next_V = next_eP - next_sP
                if curr_eP.IsAlmostEqualTo(next_sP):
                    angle = getAngle(next_eP, curr_sP, curr_eP)      
                    gap = depth * math.tan(math.radians(90) - abs(angle)/2) + .333333333333
                    new_eP = curr_eP - gap * direction

            v_list.append((new_sP, new_eP, direction))
            
            # Visualize line adjustments
            test_line = DB.Line.CreateBound(new_sP, new_eP)
            line_test = revit.doc.Create.NewDetailCurve(plan_view, test_line)
        revit.doc.Delete(listId)
else:
    only_ele = revit.doc.GetElement(lines[0])
    only_line = only_ele.Location.Curve
    direction = only_line.Direction
    only_sP = only_line.GetEndPoint(0)
    only_eP = only_line.GetEndPoint(1)

    v_list.append((only_sP, only_eP, direction))
    '''
# revit.doc.Delete(listId)
# TODO ignore line draw direction and use average of vectors to determine location @kbruxvoort



'''
with forms.WarningBar(title='Select Lines:'):
    source_elements = revit.pick_elements_by_category(DB.BuiltInCategory.OST_Lines)
    model_lines = filter(filt, source_elements)

if model_lines:
    for line in model_lines:
        print(line.Location.ElementsAtJoin[0].Item[0])
        # print(line.Location.ElementsAtJoin)[1]
        # print(line.GetAdjoinedCurveElements(1))
    
    with revit.Transaction('Find Intersections'):
        points = []
        for line in sorted(model_lines, key=lambda l: (-l.GeometryCurve.Origin.X, -l.GeometryCurve.Origin.Y)):
            # print(line.GeometryCurve.IsBound)
            print(line.GeometryCurve.Origin)
            points.append(line.GeometryCurve.GetEndPoint(0))
            points.append(line.GeometryCurve.GetEndPoint(1))
        for l1, l2 in itertools.combinations(model_lines, 2):
            intersection = get_intersection(l1.GeometryCurve, l2.GeometryCurve)
            if intersection:
                if not compare_vectors(intersection, points):
                    forms.alert("Lines cannot intersect each other", exitscript=True)
                    break
                else:
                    p1, q1 = l1.GeometryCurve.GetEndPoint(0), l1.GeometryCurve.GetEndPoint(1)
                    p2, q2 = l2.GeometryCurve.GetEndPoint(0), l2.GeometryCurve.GetEndPoint(1)
                    dp1 = p1.DistanceTo(intersection)
                    dp2 = p2.DistanceTo(intersection)
                    dq1 = q1.DistanceTo(intersection)
                    dq2 = q2.DistanceTo(intersection)
                    if dp1 > dq1:
                        v1 = p1 - q1
                    else:
                        v1 = q1 - p1
                    
                    if dp2 > dq2:
                        v2 = p2 - q2
                    else:
                        v2 = q2 - p2
 
                    # angle = v1.AngleTo(v2)
                    ccw = ccw_angle(v1, v2)

                    axis1 = v1.Normalize()
                    axis2 = DB.XYZ(-axis1.Y, axis1.X, axis1.Z)

                    new_arc = DB.Arc.Create(intersection, 1, 0, ccw, axis1, axis2)
                    # new_arc = DB.Arc.Create(intersection, 1, 0, ccw, v1.BasisX, v1.BasisY)
                    arc_test = revit.doc.Create.NewDetailCurve(plan_view, new_arc)
                    '''
                    


'''                    
with revit.Transaction('Place Cabinets'):    
    for sP, eP, direction in v_list:
        length = sP.DistanceTo(eP)
        widths = []
        min_cabinets = int(math.ceil(length/max(std_sizes)))
        # print(min_cabinets)
        for size in std_sizes:
            if length/size == min_cabinets:
                widths = [size] * min_cabinets
        
        if not widths:
            i = 0
            count = 0
            while length > 0:
                if length >= std_sizes[i]:
                    widths.append(std_sizes[i])
                    length -= std_sizes[i]  
                elif length < std_sizes[-1]:
                    # widths.insert(0, length/2)
                    # widths.append(length/2)
                    widths.append(length)
                    length -= length    
                else:
                    i += 1

        # print(widths, sum(widths))

    
        # family = clr.Reference[DB.Family]()
        # success = revit.doc.LoadFamily(path, family)
        # success, family = revit.doc.LoadFamily.Overloads.Functions[0](path)
        # print(success, family)
        fam_type = revit.query.get_family_symbol("SSG_Cabinet_Base_Open_LAM", "Default", revit.doc)
        if fam_type:
            fam_type = fam_type[0]
        if not fam_type.IsActive:
            fam_type.Activate()
            revit.doc.Regenerate()

        # fam_type_ids = family.GetValidTtypes()
        # fam_type = revit.GetElement(fam_type_ids[0])

        # sP = line.GeometryCurve.GetEndPoint(0).Normalize()
        # sP = line.GeometryCurve.GetEndPoint(0)
        # eP = line.GeometryCurve.GetEndPoint(1)
        # direction = line.GeometryCurve.Direction
        # print(direction)
        magnitude = 0
        print(widths)
        for i, width in enumerate(widths): 
            if i > 0:
                curr_width = widths[i]/2.0
                prev_width = widths[i-1]/2.0
                print(prev_width, curr_width)
                magnitude += curr_width + prev_width
            else:
                curr_width = widths[i]/2.0
                print(curr_width)
                magnitude += curr_width
            if width >= 1:
                # magnitude = sum(widths[0:i])+width/2
                print(magnitude)
                loc = sP + direction * magnitude
                # print(width, magnitude, loc)
                cabinet = revit.doc.Create.NewFamilyInstance(loc, fam_type, DB.Structure.StructuralType.NonStructural)
                p = cabinet.LookupParameter('Width')
                p.Set(width)
                axis = DB.Line.CreateBound(loc, loc.Add(DB.XYZ(0,0,1)))
                angle1 = math.degrees(DB.XYZ.BasisX.AngleTo(eP - sP))
                # angle2 = math.degrees(DB.XYZ.BasisY.AngleTo(eP - sP))
                # print(angle1, angle2)
                DB.ElementTransformUtils.RotateElement(revit.doc, cabinet.Id, axis, math.radians(angle1))
                '''                    
                    