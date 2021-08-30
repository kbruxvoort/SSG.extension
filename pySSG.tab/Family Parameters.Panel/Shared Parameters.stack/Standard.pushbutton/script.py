from pyrevit import revit
from shared_parameters import add_standards

with revit.Transaction("Add standard parameters"):
    add_standards()