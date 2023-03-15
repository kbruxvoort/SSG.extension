import config

from pyrevit import revit, DB

source_selection = config.load_configs()

if source_selection:
    for s in source_selection:
        print(s)