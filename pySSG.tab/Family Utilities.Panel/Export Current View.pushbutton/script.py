#! python3
import os

from Autodesk.Revit import DB
from Autodesk.Revit.DB import Transaction
from Autodesk.Revit.Exceptions import ArgumentException

from PIL import Image

import clr

clr.AddReference("System.Windows.Forms")
from System.Windows import Forms

PYTHONPATH = os.environ.get("PYTHONPATH")

if PYTHONPATH:

    doc = __revit__.ActiveUIDocument.Document
    view = doc.ActiveView

    SIZE_LARGE = (1800, 1186)
    SIZE_MEDIUM = (300, 198)
    SIZE_SMALL = (186, 186)

    view_templates = []
    views = DB.FilteredElementCollector(doc).OfClass(DB.View3D).ToElements()
    for view in views:
        if view.IsTemplate:
            view_templates.append(view)

    if int(doc.Application.VersionNumber) < 2019:
        view_template = [v for v in view_templates if v.Name == "SSG_3D - Image Export"]
    else:
        view_template = [v for v in view_templates if v.Name == "SSG_3D - Image Export"]

    if view_template:
        try:
            t = Transaction(doc)
            t.Start("Set View Template")
            # print(view_template[0].Id)
            view.ViewTemplateId = view_template[0].Id
            t.Commit()
        except ArgumentException as e:
            print(e)

    dialog = Forms.SaveFileDialog()
    dialog.Title = "Export current view as PNG"
    dialog.Filter = "PNG files (*.PNG)|*.PNG"

    if dialog.ShowDialog() == Forms.DialogResult.OK:
        file_name, file_ext = os.path.splitext(dialog.FileName)
        DEFAULT_IMAGE_OPTIONS = DB.ImageExportOptions()
        DEFAULT_IMAGE_OPTIONS.PixelSize = SIZE_LARGE[1]
        DEFAULT_IMAGE_OPTIONS.FilePath = dialog.FileName
        DEFAULT_IMAGE_OPTIONS.FitDirection = DB.FitDirectionType.Vertical
        DEFAULT_IMAGE_OPTIONS.HLRandWFViewsFileType = DB.ImageFileType.PNG
        DEFAULT_IMAGE_OPTIONS.ShadowViewsFileType = DB.ImageFileType.PNG
        DEFAULT_IMAGE_OPTIONS.ImageResolution = DB.ImageResolution.DPI_300
        DEFAULT_IMAGE_OPTIONS.ExportRange = DB.ExportRange.VisibleRegionOfCurrentView

        # doc.ExportImage(DEFAULT_IMAGE_OPTIONS)
        doc.ExportImage(DEFAULT_IMAGE_OPTIONS)

        im = Image.open(dialog.FileName)
        width, height = im.size
        left = int((im.width - SIZE_LARGE[0]) / 2)
        large = im.crop((left, 0, SIZE_LARGE[0] + left, SIZE_LARGE[1]))
        large.save(file_name + "_Large" + file_ext)

        medium = large.resize((SIZE_MEDIUM[0], SIZE_MEDIUM[1]))
        medium.save(file_name + "_Medium" + file_ext)

        ratio = int(SIZE_MEDIUM[0] / (SIZE_MEDIUM[1] / SIZE_SMALL[0]))
        small = medium.resize((ratio, SIZE_SMALL[0]))
        small_left = (ratio - SIZE_SMALL[0]) / 2
        small_crop = small.crop((small_left, 0, SIZE_SMALL[0] + small_left, SIZE_SMALL[0]))
        small_crop.save(file_name + "_Small" + file_ext)

else:
    print("You need to add python PYTHONPATH (python 3.8 sitepackages) to your environment variables!")
