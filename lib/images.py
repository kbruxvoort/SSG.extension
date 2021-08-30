from pyrevit.framework import Forms
from pyrevit import revit, DB


def export_current_view():
    # collect file location from user
    dialog = Forms.SaveFileDialog()
    dialog.Title = "Export current view as PNG"
    dialog.Filter = "PNG files (*.PNG)|*.PNG"

    if dialog.ShowDialog() == Forms.DialogResult.OK:

        DEFAULT_IMAGE_OPTIONS = DB.ImageExportOptions(
            PixelSize=1186,
            FilePath=dialog.FileName,
            FitDirection=DB.FitDirectionType.Vertical,
            HLRandWFViewsFileType=DB.ImageFileType.PNG,
            ShadowViewsFileType=DB.ImageFileType.PNG,
            ImageResolution=DB.ImageResolution.DPI_300,
            ExportRange=DB.ExportRange.VisibleRegionOfCurrentView,
        )

        revit.doc.ExportImage(DEFAULT_IMAGE_OPTIONS)