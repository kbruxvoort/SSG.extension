import clr
clr.AddReference('System.Windows.Forms')
clr.AddReference('IronPython.Wpf')
clr.AddReference("System.Core")

from pyrevit import script, UI, DB, revit
from parameters import SharedParameterFile, STANDARD_PARAMETERS

import wpf
from System import Windows
from System.Collections.Generic import List
from System.Collections.ObjectModel import ObservableCollection
from System.Windows.Data import IValueConverter
from System.Linq import Enumerable
from System import Guid, Enum

class ExternalDefinitionItem:
    """Helper Class for displaying selected sheets in my custom GUI."""
    def __init__(
        self,  
        name, 
        element, 
        checked=False, 
        definition_group=None, 
        description=None, 
        guid=None, 
        user_modifiable=True, 
        visible=True, 
        is_instance=False, 
        parameter_group=None, 
        parameter_type=None
    ):
        self.name = name
        self.is_checked = checked
        self.element = element
        self.definition_group = definition_group
        self.description = description
        self.guid = guid
        self.user_modifiable = user_modifiable
        self.visible = visible
        self.is_instance = is_instance
        self.parameter_group = parameter_group
        self.parameter_type = parameter_type


class ParameterGroupItem:
    def __init__(self, enum_member=None):
        self.enum_member = enum_member   
        
    def __repr__(self):
        return self.name
        
    @property
    def name(self):
        return DB.LabelUtils.GetLabelFor(self.enum_member) + " " + "({})".format(self.enum_member)

class SharedParameterItem:
    def __init__(self, name, element, parameter_group=ParameterGroupItem(DB.BuiltInParameterGroup.PG_IDENTITY_DATA), is_instance=False, exists=False):
        self.name = name
        self.element = element
        self.parameter_group = parameter_group
        self.is_instance = is_instance
        self.is_existing = exists
        

class MyWindow(Windows.Window):
    def __init__(self, xaml_filename):
        wpf.LoadComponent(self, script.get_bundle_file(xaml_filename))
        self.external_definitions = self.populate_definitions()
        self.externalDefinitionsGrid.ItemsSource = self.external_definitions
        
        self.selectedDefinitionsGrid.Items.Clear()
        self.selectedDefinitionsGrid.ItemsSource = ObservableCollection[object]()
        
        self.parameter_groups = sorted([ParameterGroupItem(pg) for pg in Enum.GetValues(DB.BuiltInParameterGroup)], key=lambda x: x.name)
        # self.parameter_groups = sorted([pg for pg in DB.BuiltInParameterGroup.GetValues(DB.BuiltInParameterGroup)], key=lambda x: x.ToString())
        self.parameter_types = sorted(set(pt.ParameterType for pt in SharedParameterFile().list_definitions()), key=lambda x: x.ToString())
        self.param_types.ItemsSource = self.parameter_types

        
    def add_definition(self, sender, args):
        fam_mgr = revit.doc.FamilyManager
        selected_list = self.selectedDefinitionsGrid.ItemsSource
        selected_definitions = self.externalDefinitionsGrid.SelectedItems
        for sd in selected_definitions:
            if sd.name not in [s.name for s in list(selected_list)]:
                # existing_param = fam_mgr.get_Parameter(Guid(sd.Guid))
                existing_param = fam_mgr.get_Parameter(sd.guid)
                if existing_param:
                    selected_list.Add(SharedParameterItem(
                        name=existing_param.Definition.Name, 
                        element=existing_param, 
                        is_instance=existing_param.IsInstance, 
                        exists=True
                    ))
                else:
                    is_existing = False
                    is_instance = False
                    selected_list.Add(SharedParameterItem(
                        name=sd.name, 
                        element=sd.element, 
                        is_instance=is_instance, 
                        exists=is_existing
                    ))

        
    def remove_definition(self, sender, args):
        selected_items = list(self.selectedDefinitionsGrid.SelectedItems)
        for item in selected_items:
            # if item.is_existing is False:
            self.selectedDefinitionsGrid.ItemsSource.Remove(item)

    # @property
    # def ParameterGroups(self):
    #     return self.parameter_groups
    
    # @property
    # def ParameterTypes(self):
    #     return self.parameter_types

    
    def populate_definitions(self):
        self.externalDefinitionsGrid.Items.Clear()
        collection = ObservableCollection[object]()
        ext_definitions = sorted(SharedParameterFile().list_definitions(), key=lambda x: (x.OwnerGroup.Name, x.Name))
        for ed in ext_definitions:
            collection.Add(ExternalDefinitionItem(
                name=ed.Name, 
                element=ed, 
                checked=False, 
                definition_group=ed.OwnerGroup.Name, 
                description=ed.Description, 
                guid=ed.GUID, 
                user_modifiable=ed.UserModifiable, 
                visible=ed.Visible, 
                is_instance=False, 
                parameter_group=None, 
                parameter_type=ed.ParameterType))
        return collection
    
    def populate_selected(self, sender, e):
        collection = self.selectedDefinitionsGrid.ItemsSource
        fam_parameters = sorted([p for p in revit.doc.FamilyManager.Parameters if p.IsShared], key=lambda x: x.Definition.Name)
        for fp in fam_parameters:
            if fp.Definition.Name not in [item.name for item in collection]:
                collection.Add(SharedParameterItem(
                    name=fp.Definition.Name, 
                    element=fp, 
                    is_instance=fp.IsInstance, 
                    parameter_group=ParameterGroupItem(fp.Definition.ParameterGroup),
                    exists=True
                ))
                
    def populate_standard(self, sender, e):
        collection = self.selectedDefinitionsGrid.ItemsSource
        existing_names = [p.Definition.Name for p in revit.doc.FamilyManager.Parameters if p.IsShared]
        for k,v in STANDARD_PARAMETERS.items():
            def_file = SharedParameterFile()
            ed = def_file.query(name=k, first_only=True)
            if ed:
                if ed.Name not in [item.name for item in collection]:
                    if ed.Name in existing_names:
                        exists = True
                    else:
                        exists = False
                    collection.Add(SharedParameterItem(
                        name=ed.Name, 
                        element=ed, 
                        is_instance=False, 
                        parameter_group=ParameterGroupItem(v),
                        exists=exists
                    ))
                
    def add_selected(self, selected):
        pass
    
    def filter_items(self, sender, e):
        # Check if the clear filter button has been pressed
        if sender.Name == "clearFilterButton":
            # Set the ItemsSource of the left data grid to the original list of external definitions
            self.param_types.SelectedValue = None
            
        param_type = self.param_types.SelectedValue
        search_text = self.filterBox.Text
        
        # Get a copy of the original list of external definitions
        filtered_items = Enumerable.ToList(self.external_definitions)
        
        # Apply the parameter type filter if a selection has been made
        if param_type is not None:
            filtered_items = Enumerable.Where(filtered_items, lambda x: x.parameter_type == param_type)
        
        # Apply the name search filter if text has been entered
        if search_text != "":
            filtered_items = Enumerable.Where(filtered_items, lambda x: search_text.lower() in x.name.lower())
        
        # Set the ItemsSource of the left data grid to the filtered list
        self.externalDefinitionsGrid.ItemsSource = filtered_items
        
    def clear_type_filter(self, sender, e):
        self.param_types.SelectedValue = None
        self.externalDefinitionsGrid.ItemsSource = self.external_definitions

    
    def target_updated(self, sender, e):
        attribute = self.selectedDefinitionsGrid.CurrentColumn.SortMemberPath
        current_value = getattr(self.selectedDefinitionsGrid.CurrentItem, attribute)
        for item in self.selectedDefinitionsGrid.SelectedItems:
            setattr(item, attribute, current_value)
            item.changed = True
        self.selectedDefinitionsGrid.Items.Refresh()
        
    
    def button_clicked(self, sender, args):
        fam_mgr = revit.doc.FamilyManager
        with revit.Transaction("Update Shared Parameters"):
            for item in self.selectedDefinitionsGrid.ItemsSource:
                if item.is_existing:
                    try:
                        if item.is_instance:
                            fam_mgr.MakeInstance(item.element)
                        else:
                            fam_mgr.MakeType(item.element)
                    except Exception as e:
                        print("Unable to change IsInstance for {}. {}".format(item.Name, e))
                    item.element.Definition.ParameterGroup = item.parameter_group.enum_member
                else:
                    fam_mgr.AddParameter(item.element, item.parameter_group.enum_member, item.is_instance)
        
        self.Close()

        
my_window = MyWindow('ui.xaml')
my_window.ShowDialog()