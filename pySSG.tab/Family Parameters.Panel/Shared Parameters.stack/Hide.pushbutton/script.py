import itertools

from pyrevit import revit, DB, UI
from pyrevit import script
from pyrevit import forms

output = script.get_output()
logger = script.get_logger()

app = revit.doc.Application

# ensure active document is a family document
forms.check_familydoc(revit.doc, exitscript=True)

sharedParametersFile = app.OpenSharedParameterFile()
sharedGroups = sharedParametersFile.Groups

selected_parameters = forms.select_family_parameters(revit.doc)

if selected_parameters:
    keyfunc = lambda x: x.Definition.ParameterType.ToString()
    data1 = sorted(selected_parameters, key=keyfunc)
    select_dict = {k: list(g) for k, g in itertools.groupby(data1, keyfunc)}
    param_types = select_dict.keys()

    existing_hidden_params = []
    family_params = revit.doc.FamilyManager.GetParameters()
    for fparam in family_params:
        if (
            fparam.IsShared
            and fparam.Definition.Name.startswith("z")
            and fparam.Definition.ParameterType.ToString() in param_types
        ):
            existing_hidden_params.append(fparam)
    data2 = sorted(existing_hidden_params, key=keyfunc)
    param_dict = {k: list(g) for k, g in itertools.groupby(data2, keyfunc)}
    # print(param_dict)

    hidden_params = []
    off_limits = ["zC", "zD", "zH", "zM", "zO", "zP", "zW"]
    for group in sharedGroups:
        for sparam in group.Definitions:
            if (
                not sparam.Visible
                and sparam.ParameterType.ToString() in param_types
                and sparam.Name not in off_limits
            ):
                hidden_params.append(sparam)
                # print sparam.Name

    keyfunc2 = lambda x: x.ParameterType.ToString()
    data3 = sorted(hidden_params, key=keyfunc2)
    hidden_dict = {k: list(g) for k, g in itertools.groupby(data3, keyfunc2)}

    # count = 0
    with revit.Transaction("Hide parameters"):
        for k, v in select_dict.items():

            if k in param_dict:
                lst = sorted(
                    [
                        i
                        for i in hidden_dict[k]
                        if i.Name not in [x.Definition.Name for x in param_dict[k]]
                    ],
                    key=lambda x: x.Name,
                )
            elif k in hidden_dict:
                lst = sorted([i for i in hidden_dict[k]], key=lambda x: x.Name)
            else:
                lst = []

            if not lst:
                message = 'No "%s" hidden parameters.' % k
                logger.error(message)

            elif len(v) > len(lst):
                message = (
                    'Not enough "%s" hidden parameters. Swapping as many as possible'
                    % k
                )
                logger.warning(message)
            else:
                message = 'Swapping all "%s" hidden parameters.' % k
                logger.success(message)

            for p1, p2 in zip(v, lst):

                if p1.Id.IntegerValue < 0:
                    message = 'Cannot hide builtin parameter "%s"' % p1.Definition.Name
                    logger.warning(message)
                    continue
                print(
                    'Replacing "{}" with Hidden Parameter ({})'.format(
                        p1.Definition.Name, p2.Name
                    )
                )
                new_param = revit.doc.FamilyManager.ReplaceParameter(
                    p1, p2, DB.BuiltInParameterGroup.INVALID, p1.IsInstance
                )
                # count += 1
                # output.update_progress(count, max_progress)
    print("Done")