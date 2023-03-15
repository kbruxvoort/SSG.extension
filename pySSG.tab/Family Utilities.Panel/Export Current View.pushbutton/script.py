import os
import System

from datetime import datetime
from pyrevit import revit, DB, forms, script

import export_config


def get_extension(image_type):
    if image_type == DB.ImageFileType.BMP:
        return ".bmp"
    elif image_type == DB.ImageFileType.PNG:
        return ".png"
    elif image_type == DB.ImageFileType.TARGA:
        return ".targa"
    elif image_type == DB.ImageFileType.TIFF:
        return ".tiff"
    return ".jpg"

def get_selection_bounding_box(selection, view, offset=0):
    min_x, min_y, min_z = [], [], []
    max_x, max_y, max_z = [], [], []
    for s in selection:
        bbox = s.get_BoundingBox(view)
        min_x.append(bbox.Min.X)
        min_y.append(bbox.Min.Y)
        min_z.append(bbox.Min.Z)
        max_x.append(bbox.Max.X)
        max_y.append(bbox.Max.Y)
        max_z.append(bbox.Max.Z)
    
    new_min = DB.XYZ(min(min_x) - offset, min(min_y) - offset, min(min_z) - offset)
    new_max = DB.XYZ(max(max_x) + offset, max(max_y) + offset, max(max_z) + offset)
    
    new_bbox = DB.BoundingBoxXYZ()
    new_bbox.Min = new_min
    new_bbox.Max = new_max
    return new_bbox


pixel_default = 1080
# my_config = script.get_config()

values = export_config.load_configs()

try:
    pixel_size = int(values.get('pixel_size', pixel_default))
except ValueError:
    pixel_size = pixel_default
    
picture_folder_path = System.Environment.GetFolderPath(System.Environment.SpecialFolder.MyPictures)
current_datetime = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
filepath = os.path.join(picture_folder_path, current_datetime)

selection = revit.pick_elements('Choose objects to export')
# selection = UI.Selection.Selection.PickObjects(UI.Selection.ObjectType.Element)


if selection:
    open_views = revit.uidoc.GetOpenUIViews()
    if open_views:
        options = DB.ImageExportOptions()
        options.PixelSize = pixel_size
        options.FilePath = filepath
        options.FitDirection = values.get("fit_direction")
        options.HLRandWFViewsFileType = values.get("file_type")
        options.ShadowViewsFileType = values.get("file_type")
        options.ImageResolution = values.get("image_resolution")
        options.ExportRange = values.get("export_range")
        with revit.TransactionGroup("Export Selection Image"):
            with revit.Transaction("Create Group View"):
                starting_view = revit.active_view
                offset = 1/12
                bbox = get_selection_bounding_box(selection, starting_view, offset)
                
                view_type_id = revit.doc.GetDefaultElementTypeId(DB.ElementTypeGroup.ViewType3D)
                threeD = DB.View3D.CreateIsometric(revit.doc, view_type_id)
                threeD.IsSectionBoxActive = True
                threeD.SetSectionBox(bbox)
                threeD.Name = "Image_Export"
                # if template_id:
                #     threeD.ViewTemplateId = template_id 
                
            
            revit.uidoc.ActiveView = threeD
            revit.uidoc.GetOpenUIViews()[0].ZoomToFit()
            
            with revit.Transaction("Export Image"):
                forms.alert('Image saved to "{}"'.format(filepath + get_extension(values.get("file_type"))), warn_icon=False, )
                revit.doc.ExportImage(options)
            
            if values.get("delete_view"):
                revit.uidoc.ActiveView = starting_view
                with revit.Transaction("Delete View"):
                    revit.doc.Delete(threeD.Id)
