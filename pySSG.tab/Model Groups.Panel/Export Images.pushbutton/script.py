"""
This script exports images for each group in the active view. The groups are exported as a png.
"""

#pylint: disable=import-error,invalid-name,broad-except
import clr
# Import RevitAPI
clr.AddReference("RevitAPI")
import Autodesk
from Autodesk.Revit.DB import *

# import System
# from System import Array
# from System.Collections.Generic import *

from pyrevit import revit, DB, UI
from pyrevit import script
from pyrevit import forms	
from pyrevit import HOST_APP

__title__ = "Export\nGroup Images"
__author__ = "{{author}}"

logger = script.get_logger()
output = script.get_output()


threeD_view = revit.doc.ActiveView 

forms.check_viewtype(threeD_view, ViewType.ThreeD, exitscript=True)

target_folder = forms.pick_folder(title='Select Image Save Location')

groups = FilteredElementCollector(revit.doc).OfClass(Group).WhereElementIsNotElementType().ToElements()


total_work = len(groups)
viewTypeId = threeD_view.GetTypeId()
if target_folder:
    for idx, group in enumerate(groups):
        

        viewSet = []
        # Get group Bounding Box and Create New 
        groupBB = group.get_BoundingBox(threeD_view)
        gMax = groupBB.Max
        gMin = groupBB.Min
        height = XYZ(0, 0, gMax.Z).DistanceTo(XYZ(0, 0, gMin.Z))
        # print(height)
        width = XYZ(gMax.X, 0, 0).DistanceTo(XYZ(gMin.X, 0, 0))
        # print(width)
        # if height > width:
        #     newWidth = height/2*1.5177
        #     centerX = (gMin.X + gMax.X) / 2
        #     newMaxP = XYZ(centerX + newWidth + 1, gMax.Y + 1, gMax.Z + 1)
        #     newMinP = XYZ(centerX - newWidth - 1, gMin.Y - 1, gMin.Z - 1)
        # else: 
        #     newMaxP = XYZ(gMax.X + 1, gMax.Y + 1, gMax.Z + 1)
        #     newMinP = XYZ(gMin.X - 1, gMin.Y - 1, gMin.Z - 1)
        newMaxP = XYZ(gMax.X + 1, gMax.Y + 1, gMax.Z + 1)
        newMinP = XYZ(gMin.X - 1, gMin.Y - 1, gMin.Z - 1)
        newBB = BoundingBoxXYZ()
        newBB.Max = newMaxP
        newBB.Min = newMinP

        ieo = ImageExportOptions(
            PixelSize = 1186,
            FilePath = target_folder + "\\" + group.Name,
            FitDirection = FitDirectionType.Vertical,
            HLRandWFViewsFileType = ImageFileType.PNG,
            ShadowViewsFileType = ImageFileType.PNG,
            ImageResolution = ImageResolution.DPI_300,
            # ExportRange = ExportRange.SetOfViews
            ExportRange = ExportRange.VisibleRegionOfCurrentView
            )

        with revit.Transaction("Create Group View"):
            threeD = View3D.CreateIsometric(revit.doc, viewTypeId)
            View3D.SetSectionBox(threeD, newBB)
            threeD.Name = group.Name
        
        uidoc = HOST_APP.uiapp.ActiveUIDocument
        uidoc.ActiveView = threeD

        with revit.Transaction("Export Group Image"):
            print('Saving PNG "%s" to %s' % (group.Name, target_folder + "\\" + group.Name))
            revit.doc.ExportImage(ieo)

    

        output.update_progress(idx + 1, total_work)

print("Completed\n")