from pyrevit import script, forms

from pyrevit import forms

my_config = script.get_config("override cropbox")

result = forms.ask_for_number_slider(
    default=my_config.get_option("line_weight", 6),
    min=1,
    max=10,
    interval=1,
    prompt='Select a number:',
    title='Cropbox Override Settings'
)

if result:
    my_config.line_weight = result
    script.save_config()
# slider_form = forms.GetValueWindow()

# slider_form.show(
#     None,
#     value_type='slider',
#     default=5,
#     prompt='Select a number:',
#     title='Cropbox Override Settings',
#     min=1,
#     max=10,
#     step=1
#     )

# if result:
#     print(result)

'''
from rpw.ui.forms import (
    FlexForm, 
    Label, 
    ComboBox, 
    TextBox, 
    Separator, 
    Button, 
    CheckBox
)


my_config = script.get_config("override cropbox")


def load_configs():
    values = {}
    values["export_range"] = getattr(DB.ExportRange, my_config.get_option('export_range', str(DB.ExportRange.VisibleRegionOfCurrentView)))
    values["pixel_size"] = my_config.get_option('pixel_size', "1080")
    values["fit_direction"] = getattr(DB.FitDirectionType, my_config.get_option('fit_direction', str(DB.FitDirectionType.Vertical)))
    values["file_type"] = getattr(DB.ImageFileType, my_config.get_option('file_type', str(DB.ImageFileType.JPEGLossless)))
    values["image_resolution"] = getattr(DB.ImageResolution, my_config.get_option('image_resolution', str(DB.ImageResolution.DPI_300)))
    values["delete_view"] = my_config.get_option('delete_view', False)
    # values["template_id"] = revit.doc.GetElement(DB.ElementId(int(my_config.get_option('template_id'))))
    return values

def save_configs(values):
    my_config.export_range = str(values["export_range"])
    my_config.pixel_size = int(values['pixel_size'])
    my_config.fit_direction = str(values['fit_direction'])
    my_config.file_type = str(values['file_type'])
    my_config.image_resolution = str(values['image_resolution'])
    my_config.delete_view = values['delete_view']
    # my_config.template_id = str(values['template_id'])
    script.save_config()
    
def config_menu():
    prev_config = load_configs()
    # threeD_views = DB.FilteredElementCollector(revit.doc).OfClass(DB.View3D).ToElements()
    # templates = {v.Name: v for v in threeD_views if v.IsTemplate}
    
    components = [
        Label('Export Range:'),
        ComboBox(
            'export_range',
            {
                str(DB.ExportRange.CurrentView): DB.ExportRange.CurrentView, 
                str(DB.ExportRange.VisibleRegionOfCurrentView): DB.ExportRange.VisibleRegionOfCurrentView
            }, 
            default=str(prev_config.get("export_range", str(DB.ExportRange.VisibleRegionOfCurrentView)))),
        Label('Pixel Size:'),
        TextBox('pixel_size', 
                Text=str(prev_config.get("pixel_size", 1080))),
        Label('Fit Direction:'),
        ComboBox('fit_direction', {
            str(DB.FitDirectionType.Vertical): DB.FitDirectionType.Vertical, 
            str(DB.FitDirectionType.Horizontal): DB.FitDirectionType.Horizontal}, 
            default=str(prev_config.get("fit_direction", str(DB.FitDirectionType.Vertical)))),
        Label('File Type:'),
        ComboBox('file_type', {
            str(DB.ImageFileType.BMP): DB.ImageFileType.BMP, 
            str(DB.ImageFileType.JPEGLossless): DB.ImageFileType.JPEGLossless, 
            str(DB.ImageFileType.JPEGMedium): DB.ImageFileType.JPEGMedium,
            str(DB.ImageFileType.JPEGSmallest): DB.ImageFileType.JPEGSmallest,
            str(DB.ImageFileType.PNG): DB.ImageFileType.PNG,
            str(DB.ImageFileType.TARGA): DB.ImageFileType.TARGA,
            str(DB.ImageFileType.TIFF): DB.ImageFileType.TIFF
            }, 
            default=str(prev_config.get("file_type", str(DB.ImageFileType.JPEGLossless)))),
        Label('Raster Image Quality:'),
        ComboBox('image_resolution', {
            str(DB.ImageResolution.DPI_72): DB.ImageResolution.DPI_72, 
            str(DB.ImageResolution.DPI_150): DB.ImageResolution.DPI_150,
            str(DB.ImageResolution.DPI_300): DB.ImageResolution.DPI_300,
            str(DB.ImageResolution.DPI_600): DB.ImageResolution.DPI_600}, 
            default = str(prev_config.get("image_resolution", str(DB.ImageResolution.DPI_300)))),
        CheckBox('delete_view', 
                 'Delete 3D View after export', 
                 default=prev_config.get('delete_view', False)),
        # Separator(),
        # Label('View Template:'),
        # ComboBox('template_id', templates, default=prev_config['template_id']),
        Button('Select')
    ]
     
    form = FlexForm('Image Export Options', components)
    form.show()

    if form.values:
        save_configs(form.values)
    return form.values


if __name__ == "__main__":
    config_menu()
'''