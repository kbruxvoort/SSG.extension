"""Shift Click Test"""
#pylint: disable=E0401,C0103
from pyrevit import forms, script, revit

my_config = script.get_config()

class SharedParamItem(forms.TemplateListItem):
    """Wrapper class for shared parameter list item"""
    pass
    
    @property
    def name(self):
        """View type name."""
        return self.item.Name


def load_configs():
    selection_config = my_config.get_option('selection_config',[])
    return selection_config

def save_configs(selection_item):
    # my_config.selection_config = [x for x in selection_item]
    my_config.selection_config = selection_item
    script.save_config()

def config_menu():
    prev_config = load_configs()
    # item_list = ["item 1", "item 2"]
    # type_name = "elevation"
    # view_types = [revit.query.get_name(x) for x in revit.query.get_types_by_class(DB.ViewFamilyType) if x.ViewFamily == DB.ViewFamily.Elevation]
    definition_file = revit.doc.Application.OpenSharedParameterFile()
    if definition_file:
        shared_params = []
        
        for group in definition_file.Groups:
            for definition in group.Definitions:
                shared_params.append(definition)
            
    selection_config = forms.SelectFromList.show(
        [SharedParamItem(x, checked = x in prev_config) for x in shared_params], 
        # name_attr='Name',
        title = 'Shared Parameters', 
        button_name = "Select Shared Parameters", 
        multiselect = True
    )
    # selected = forms.SelectFromList.show(
    #         sorted([ViewTypeItem(x) for x in rooms], key=lambda x: x.Number),
    #         multiselect=True,
    #         # name_attr= 'Number',
    #         button_name="Select Rooms",
    #     )
    if selection_config:
        save_configs(selection_config)
    return selection_config

if __name__ == "__main__":
    config_menu()