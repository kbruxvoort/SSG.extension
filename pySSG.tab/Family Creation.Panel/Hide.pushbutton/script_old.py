"""
This script replaces selected family parameters with a generic 
hidden shared parameter.
"""

import clr
clr.AddReference("RevitAPI")
from Autodesk.Revit.DB import *
from pyrevit import revit, DB, UI
from pyrevit import script
from pyrevit import forms
import System
from System.Collections.Generic import *

__title__ = "Swap for\nHidden"
__author__ = "{{author}}"

def share_match(share_file, name):
    for group in share_file.Groups:
        for shared_param in group.Definitions:
            if name == shared_param.Name:
                return shared_param
            else:
                pass


logger = script.get_logger()

app = revit.doc.Application

# ensure active document is a family document
forms.check_familydoc(revit.doc, exitscript=True)
    
sharedParametersFile = app.OpenSharedParameterFile()
sharedGroups = sharedParametersFile.Groups

selected_parameters = forms.select_family_parameters(revit.doc)


angles, areas, yesnos, currencies, integers, lengths, numbers, texts = [], [], [], [], [], [], [], []
big_list = []

if selected_parameters:
    for r in selected_parameters:
        if r.Definition.ParameterType.ToString() == "Angle":
            angles.append(r)
        elif r.Definition.ParameterType.ToString() == "Area":
            areas.append(r)
        elif r.Definition.ParameterType.ToString() == "YesNo":
            yesnos.append(r)
        elif r.Definition.ParameterType.ToString() == "Currency":
            currencies.append(r)
        elif r.Definition.ParameterType.ToString() == "Integer":
            integers.append(r)
        elif r.Definition.ParameterType.ToString() == "Length":
            lengths.append(r)
        elif r.Definition.ParameterType.ToString() == "Number":
            numbers.append(r)
        elif r.Definition.ParameterType.ToString() == "Text":
            texts.append(r)
        else:
            message = '"{}" is an unsupported parameter type ({})'.format(r.Definition.Name, r.Definition.ParameterType.ToString())
            logger.warning(message)

big_list.append(angles)
big_list.append(areas)
big_list.append(yesnos)
big_list.append(currencies)
big_list.append(integers)
big_list.append(lengths)
big_list.append(numbers)
big_list.append(texts)

data_types = {
    "Angle": "zA",
    "Area": "zAR",
    "YesNo": "zB",
    "Currency": "zCU",
    "Integer": "zI",
    "Length": "zL",
    "Number": "zNU",
    "Text": "zPT"
}

shared_names = []
old_params = []
for t_list in big_list:
    for idx, param in enumerate(t_list):
        for key, value in data_types.items():
            if param.Definition.ParameterType.ToString() == key:
                old_params.append(param)
                if idx < 10:
                    shared_name = value + "0" + str(idx)
                    shared_names.append(shared_name)
                else:
                    shared_name = value + str(idx)
                    shared_names.append(shared_name)
                    
old_list = []                        
with revit.Transaction("Hide parameters"):
    for n, r in zip(shared_names, old_params):
        s = share_match(sharedParametersFile, n)
        # if builtin, reset values and skip delete
        if r.Id.IntegerValue < 0:
            message = \
                'Cannot hide builtin "%s"' % r.Definition.Name
            logger.warning(message)
            continue
        if r.IsShared:
            message = \
                '"%s" is a shared parameter' % r.Definition.Name
            logger.warning(message)
            continue    
        try:
            old_name = r.Definition.Name           
            new_param = revit.doc.FamilyManager.ReplaceParameter(r, s, BuiltInParameterGroup.INVALID, r.IsInstance)
            print('Replacing "{}" with Hidden Parameter ({})'.format(old_name, new_param.Definition.Name))
            # count += 1            
            # # logger.log_success("Successfully Hidden")
            # old_list.append(old_name)
            # success_list.append(new_param)
        except:
            logger.error(old_name + " failed to hide")




