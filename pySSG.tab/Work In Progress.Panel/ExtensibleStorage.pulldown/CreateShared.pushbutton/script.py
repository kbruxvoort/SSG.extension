import itertools

from System import Guid

from pyrevit import revit, DB, HOST_APP, forms

from Autodesk.Revit.Exceptions import InvalidOperationException

from parameters.shared import get_shared_groups, query_shared

class ParamItem(forms.TemplateListItem):
    """Wrapper class for frequently selected external definition"""
    pass

    @property
    def name(self):
        return self.Definition.Name

"""
group_name = 'pySSG'
groups = get_shared_groups(revit.doc.Application)
# group by name
group = [g for g in groups if g.Name == group_name]

# create group
if not group:
    try:
        group = groups.Create(group_name)
    except InvalidOperationException:
        print('Group name already exists') 
    else:
        print(group.Name, group.Definitions)
else:
    group = group[0]
print(group.Definitions)

# create definition
if HOST_APP.is_newer_than(2020):
    options = DB.ExternalDefinitionCreationOptions('zIsHidden', DB.SpecTypeId.Boolean.YesNo)
else:
    options = DB.ExternalDefinitionCreationOptions('zIsHidden', DB.ParameterType.YesNo)
options.Description = 'API Hidden Test'
options.GUID = Guid('e07795d7-172e-4592-95d8-0cde5120d361')
options.Visible = False
group.Definitions.Create(options)
"""
# get potential parameters for hiding
mgr = revit.doc.FamilyManager
params = mgr.GetParameters()
hideable_params = [p for p in params if not p.IsShared and p.Id.IntegerValue > 0]

# user selects parameters to hide
selected_params = forms.SelectFromList.show(
    sorted([ParamItem(x) for x in hideable_params], key=lambda x: x.Definition.Name),
    title='Select Parameters to Hide',
    button_name='Apply',
    multiselect=True,
)

# group by parameter type
if selected_params:
    print('selected parameters')
    if HOST_APP.is_newer_than(2020):
        key_func = lambda x: x.Definition.GetDataType()
        key_func2 = lambda x: x.GetDataType()
        
        for key, group in itertools.groupby(sorted(selected_params, key=key_func), key_func):
            params = list(group)
            print(key.TypeId, len(params), sorted([p.Definition.Name for p in params]))
    else:
        key_func = lambda x: x.Definition.ParameterType
        key_func2 = lambda x: x.ParameterType
        for key, group in itertools.groupby(selected_params, key_func):
            params = list(group)
            print(key, len(params), sorted([p.Definition.Name for p in params]))
    
    app = revit.doc.Application
    print('-----------------')
    print('hidden parameters')
    hidden_shared = query_shared(app, name='z', hidden=True)
    # for hs in sorted(hidden_shared, key=lambda x: x.GetDataType().GetHashCode()):
    #     print(hs.GetDataType(), hs.Name)
    for key, group in itertools.groupby(sorted(hidden_shared, key=key_func2), key_func2):
        params = list(group)
        print(key, len(params), sorted([p.Name for p in params]))
    # for key, group in itertools.groupby(hidden_shared, key_func2):
    # test = itertools.groupby(hidden_shared, key_func2)
    # hidden_dict = {}
    # for key, group in test:
    #     hidden_dict[key] = list([g.Name for g in group])
    # print(hidden_dict)
    # #     print(key, list([g.Name for g in group]))      