from pyrevit import forms, script, HOST_APP, DB

_config = script.get_config()
# print(_config)

elevation = forms.select_views(
    title='Select views',
    filterfunc=lambda x: x.ViewType == DB.ViewType.Elevation
)

_config.get_option('View', elevation)

script.save_config()