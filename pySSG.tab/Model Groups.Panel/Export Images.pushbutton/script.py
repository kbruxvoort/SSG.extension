# pylint: disable=import-error,invalid-name,broad-except
from pyrevit import revit, DB
from pyrevit import script
from pyrevit import forms
from pyrevit import HOST_APP


logger = script.get_logger()
output = script.get_output()


threeD_view = revit.doc.ActiveView

# forms.check_viewtype(threeD_view, ViewType.ThreeD, exitscript=True)

groups = (
    DB.FilteredElementCollector(revit.doc)
    .OfClass(DB.Group)
    .WhereElementIsNotElementType()
    .ToElements()
)

total_work = len(groups)
# print(total_work)

if total_work > 0:
    target_folder = forms.pick_folder(title="Select Image Save Location")
    if target_folder:
        viewTypeId = threeD_view.GetTypeId()
        for idx, group in enumerate(groups):

            viewSet = []
            # Get group Bounding Box and Create New
            groupBB = group.get_BoundingBox(threeD_view)
            gMax = groupBB.Max
            gMin = groupBB.Min
            height = DB.XYZ(0, 0, gMax.Z).DistanceTo(DB.XYZ(0, 0, gMin.Z))
            # print(height)
            width = DB.XYZ(gMax.X, 0, 0).DistanceTo(DB.XYZ(gMin.X, 0, 0))
            # print(width)
            # if height > width:
            #     newWidth = height/2*1.5177
            #     centerX = (gMin.X + gMax.X) / 2
            #     newMaxP = XYZ(centerX + newWidth + 1, gMax.Y + 1, gMax.Z + 1)
            #     newMinP = XYZ(centerX - newWidth - 1, gMin.Y - 1, gMin.Z - 1)
            # else:
            #     newMaxP = XYZ(gMax.X + 1, gMax.Y + 1, gMax.Z + 1)
            #     newMinP = XYZ(gMin.X - 1, gMin.Y - 1, gMin.Z - 1)
            newMaxP = DB.XYZ(gMax.X + 1, gMax.Y + 1, gMax.Z + 1)
            newMinP = DB.XYZ(gMin.X - 1, gMin.Y - 1, gMin.Z - 1)
            newBB = DB.BoundingBoxXYZ()
            newBB.Max = newMaxP
            newBB.Min = newMinP

            ieo = DB.ImageExportOptions(
                PixelSize=1186,
                FilePath=target_folder + "\\" + group.Name,
                FitDirection=DB.FitDirectionType.Vertical,
                HLRandWFViewsFileType=DB.ImageFileType.PNG,
                ShadowViewsFileType=DB.ImageFileType.PNG,
                ImageResolution=DB.ImageResolution.DPI_300,
                # ExportRange = ExportRange.SetOfViews
                ExportRange=DB.ExportRange.VisibleRegionOfCurrentView,
            )

            with revit.Transaction("Create Group View"):
                threeD = DB.View3D.CreateIsometric(revit.doc, viewTypeId)
                DB.View3D.SetSectionBox(threeD, newBB)
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