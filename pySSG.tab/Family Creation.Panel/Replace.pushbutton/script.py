"""
This script replaces all family parameters that have the same
name as a shared parameter.
"""

from pyrevit import revit, DB, UI
from pyrevit import script
from pyrevit import forms


__title__ = "Replace\nfor Shared"
__author__ = "{{author}}"

logger = script.get_logger()

# ensure active document is a family document
forms.check_familydoc(revit.doc, exitscript=True)

app = revit.doc.Application

# make sure user has saved open models in case the tool crashes
if not forms.alert('Make sure your models are saved and synced. '
                   'Hit OK to continue...', cancel=True):
    script.exit()
   
# filepath = forms.pick_file(file_ext='txt')
# if filepath:
#     app.SharedParametersFilename = filepath
#     sharedParametersFile = app.OpenSharedParameterFile()
#     sharedGroups = sharedParametersFile.Groups
# else:
#     forms.alert('You must select a file', exitscript=True)
sharedParametersFile = app.OpenSharedParameterFile()
sharedGroups = sharedParametersFile.Groups

family_params = revit.doc.FamilyManager.GetParameters()

replace_list = []
shared_list = []

for group in sharedGroups:
    for sparam in group.Definitions:
        for fparam in family_params:
            if not fparam.IsShared:
                if fparam.Definition.Name == sparam.Name:
                    if fparam.Definition.ParameterType == sparam.ParameterType:
                        replace_list.append(fparam)
                        shared_list.append(sparam)

# define a transaction variable and describe the transaction
with revit.Transaction("Replace parameters"):
    for r, s in zip(replace_list, shared_list):
        try:
            print('Replacing "{}" with Shared Parameter ({})'.format(r.Definition.Name, s.Name))
            # Revit doesn't like it if the old parameter has the same name as the new one so we much change it first
            revit.doc.FamilyManager.RenameParameter(r, r.Definition.Name + "_Old")
            new_param = revit.doc.FamilyManager.ReplaceParameter(r, s, r.Definition.ParameterGroup, r.IsInstance)                
        except:
            logger.error('Failed to Replace "{}"'.format(r.Definition.Name))
            # logger.error('Failed to Replace Parameter')


    print('Done')



