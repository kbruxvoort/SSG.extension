"""
This script is the initial test for creating a faster way 
to reorder parameters. Currently it just sorts them by length 
of parameter name. (Largest to Smallest)
"""

from pyrevit import revit, DB
from pyrevit import script
from pyrevit import forms

__title__ = "Reorder\nParameters"
__author__ = "{{author}}"

# ensure active document is a family document
forms.check_familydoc(revit.doc, exitscript=True)

# get current parameters
params = revit.doc.FamilyManager.GetParameters()

# sort parameters by a function - length of name from largest to smallest
new_list = sorted(params, key=lambda x: len(x.Definition.Name), reverse=True)


# define a transaction variable and describe the transaction
with revit.Transaction("Reorder parameters"):
    try:
        revit.doc.FamilyManager.ReorderParameters(new_list)
    except:
        Exception

print "New Parameter Order:"
for param in new_list:
    print "....." + param.Definition.Name