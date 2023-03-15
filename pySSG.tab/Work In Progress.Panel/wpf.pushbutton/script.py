import clr
clr.AddReference("System.Windows.Forms")
clr.AddReference("System")
from System.Collections.Generic import List

from pyrevit import forms, DB, UI
from pyrevit.revit import doc


def print_data(data):
    if data.get('Materials'):
        print('Materials:')
        for mat in data['Materials']:
            print("\t[{}] {}".format(mat.Id, mat.Name))
            
    if data.get('Parameters'):
        print('Parameters:')
        for param in data['Parameters']:
            print(param.IsShared)
            print("\t[{}] {} IsBuiltIn: {}".format(param.Id, param.Definition.Name, not(param.Definition.BuiltInParameter==DB.BuiltInParameter.INVALID)))
    
# from GUI.forms import my_WPF, ListItem

# PATH_SCRIPT = os.path.dirname(__file__)
# xamlfile = script.get_bundle_file('ui.xaml')
class ListItem:
    """Helper Class for displaying selected sheets in my custom GUI."""
    def __init__(self,  Name='Unnamed', element = None, checked = False):
        self.Name       = Name
        self.IsChecked  = checked
        self.element    = element
        
class ParameterListItem:
    def __init__(self,  Name='Unnamed', element = None, checked = False, instance=False):
        self.Name       = Name
        self.IsChecked  = checked
        self.element    = element
        self.IsInstance = instance
        # self.IsInstance = "Instance" if instance else "Type"

# class MyWindow(my_WPF):
class MyWindow(forms.WPFWindow):
    def __init__(self, xaml_file_name):
        forms.WPFWindow.__init__(self, xaml_file_name)
        self.response = None
        self.list_materials = self.generate_list_materials()
        self.list_parameters = self.generate_list_parameters()
        self.UI_ListBox_Materials.ItemsSource = self.list_materials
        self.UI_ListBox_Parameters.ItemsSource = self.list_parameters
        

        
    def generate_list_materials(self):
        list_items = List[type(ListItem())]()
        all_materials = DB.FilteredElementCollector(doc).OfClass(DB.Material).ToElements()
        dict_materials = {mat.Name: mat for mat in all_materials}

        for mat_name, mat in sorted(dict_materials.items()):
            list_items.Add(ListItem(mat_name, mat, False))
        return list_items
    
    def generate_list_parameters(self):
        param_list = List[type(ParameterListItem())]()
        all_parameters = doc.FamilyManager.GetParameters()
        dict_parameters = {param.Definition.Name: param for param in all_parameters}
        
        for param_name, param in sorted(dict_parameters.items()):
            param_list.Add(ParameterListItem(param_name, param, False, param.IsInstance))
        return param_list
    
        
    def button_select(self, sender, args):
        self.response = {
            "Materials": [item.element for item in self.UI_ListBox_Materials.ItemsSource if item.IsChecked],
            "Parameters": [item.element for item in self.UI_ListBox_Parameters.ItemsSource if item.IsChecked]
        }
        self.Close()
        print_data(self.response)
        
        
    @property
    def user_name(self):
        return self.my_name.Text
    
    def say_hello(self, sender, args):
        self.Close()
        UI.TaskDialog.Show('Hello World!', "Hello {}".format(self.user_name or 'World'))
        
    def text_filter_updated(self, sender, e):
        """Function to filter items in the main_ListBox."""
        filtered_list_materials = List[type(ListItem())]()
        filter_keyword = self.textbox_filter.Text

        #RESTORE ORIGINAL LIST
        if not filter_keyword:
            self.UI_ListBox_Materials.ItemsSource = self.list_materials
            return

        # FILTER ITEMS
        for item in self.list_materials:
            if filter_keyword.lower() in item.Name.lower():
                filtered_list_materials.Add(item)

        # UPDATE LIST OF ITEMS
        self.UI_ListBox_Materials.ItemsSource = filtered_list_materials
    
    def update_list_items(self, new_list):    
        self.UI_ListBox_Materials.ItemsSource = new_list
        
        
if __name__ == '__main__':
    MyWindow('publish.xaml').show(modal=True)

