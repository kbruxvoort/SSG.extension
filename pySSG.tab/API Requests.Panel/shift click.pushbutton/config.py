"""Shift Click Test"""
#pylint: disable=E0401,C0103
from pyrevit import forms, script, revit, DB
from parameters import shared

my_config = script.get_config("add_standard_params")

class SharedParamItem(forms.TemplateListItem):
    """Wrapper class for view type list item"""
    pass
    
    # @property
    # def name(self):
    # #     """View type name."""
    #     return "%s" % self.Definition.Name


def load_configs():
    """Load list of frequently selected parameters from configs or defaults"""
    param_names = my_config.get_option('standard_params', [])
    standard_params = [shared.query(revit.doc.Application, name=n) for n in (param_names or shared.STANDARD_PARAMETERS.keys())]
    
    return filter(None, standard_params)

def save_configs(params):
    my_config.standard_params = [x.Name for x in params]
    script.save_config()

def config_params():
    prev_params = load_configs()
    all_params = shared.query(revit.doc.Application)
    prev_params = [x.Name for x in prev_params]
    standard_params = forms.SelectFromList.show(
        sorted(
            [SharedParamItem(x,
                             checked=x.Name in prev_params,
                             name_attr='Name')
             for x in all_params],
            key=lambda x: x.name
        ),
        title='Select Standard Parameters',
        button_name='Apply',
        multiselect=True,
    )
    if standard_params:
        save_configs(standard_params)
    return standard_params
    # item_list = ["item 1", "item 2"]
    # type_name = "elevation"
    # view_types = [revit.query.get_name(x) for x in revit.query.get_types_by_class(DB.ViewFamilyType) if x.ViewFamily == DB.ViewFamily.Elevation]
    # selection_config = forms.SelectFromList.show([ViewTypeItem(x, checked = x in prev_config) for x in view_types], title = 'Elevation Types', button_name = "Select Elevation Type", multiselect = False)
    # selected = forms.SelectFromList.show(
    #         sorted([ViewTypeItem(x) for x in rooms], key=lambda x: x.Number),
    #         multiselect=True,
    #         # name_attr= 'Number',
    #         button_name="Select Rooms",
    #     )
    # if selection_config:
    #     save_configs(selection_config)
    # return selection_config
    # data = {
    #     "string": "The Answer",
    #     "bool": True,
    #     "int": 420,
    #     }
    # save_configs(data)
    # return data

if __name__ == "__main__":
    config_params()