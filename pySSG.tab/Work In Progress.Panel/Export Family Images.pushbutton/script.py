# pylint: disable=import-error,invalid-name,broad-except
import clr


clr.AddReference("System")
clr.AddReference("System.IO")
clr.AddReference("System.Drawing")

from System import IO
from System.Drawing import GraphicsUnit, Graphics, Rectangle, Bitmap

from pyrevit import revit, DB, UI, script, forms, HOST_APP
from kyle_test import get_outline

# from pyrevit import script
# from pyrevit import forms
# from pyrevit import HOST_APP


logger = script.get_logger()
output = script.get_output()


threeD_view = revit.doc.ActiveView

# forms.check_viewtype(threeD_view, ViewType.ThreeD, exitscript=True)


target_folder = forms.pick_folder(title="Select Image Save Location")
if target_folder:
    viewTypeId = threeD_view.GetTypeId()
    selection = revit.get_selection()
    # party()

    """
    for s in selection:
        print(s)

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
            PixelSize=1186,
            FilePath=target_folder + "\\" + group.Name,
            FitDirection=FitDirectionType.Vertical,
            HLRandWFViewsFileType=ImageFileType.PNG,
            ShadowViewsFileType=ImageFileType.PNG,
            ImageResolution=ImageResolution.DPI_300,
            # ExportRange = ExportRange.SetOfViews
            ExportRange=ExportRange.VisibleRegionOfCurrentView,
        )

        with revit.Transaction("Create Group View"):
            threeD = View3D.CreateIsometric(revit.doc, viewTypeId)
            View3D.SetSectionBox(threeD, newBB)
            threeD.Name = group.Name

        uidoc = HOST_APP.uiapp.ActiveUIDocument
        uidoc.ActiveView = threeD

        with revit.Transaction("Export Group Image"):
            print(
                'Saving PNG "%s" to %s'
                % (group.Name, target_folder + "\\" + group.Name)
            )
            revit.doc.ExportImage(ieo)

        output.update_progress(idx + 1, total_work)

    print("Completed\n")
else:
    message = "There are no model groups in this project"
    logger.warning(message)
    """
