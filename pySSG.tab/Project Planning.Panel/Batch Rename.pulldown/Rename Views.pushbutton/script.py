"""
This script allows the user to batch rename views. User has the option to use regular expressions and ignore case.
"""

# dependencies
import clr
import re
clr.AddReference('System.Windows.Forms')
clr.AddReference('IronPython.Wpf')
clr.AddReference('RevitAPI')

from Autodesk.Revit.Exceptions import ArgumentException
# find the path of ui.xaml
from pyrevit import revit, DB, UI
from pyrevit import script
from pyrevit import forms
xamlfile = script.get_bundle_file('ui.xaml')

# import WPF creator and base Window
import wpf
from System import Windows

__title__ = " Batch rename views"
__author__ = "{{author}}"

class ViewOption(forms.TemplateListItem):
    # def __init__(self, room_element):
    #     super(RoomOption, self).__init__(room_element)

    @property
    def name(self):
        """ViewType: View Name."""
        return '{}: {}'.format(self.item.ViewType, revit.query.get_name(self.item))

class MyWindow(Windows.Window):
    def __init__(self):
        wpf.LoadComponent(self, xamlfile)

    @property
    def use_regex(self):
        return self.regexToggle.IsChecked

    @property
    def use_ignorecase(self):
        return self.caseToggle.IsChecked
    

    # def toggle_regex(self, sender, args):
    #     self.regexToggle.Content = \
    #         self.Resources['regexIcon'] if self.use_regex \
    #             else self.Resources['filterIcon']
    #     self.search_txt_changed(sender, args)
    #     self.search_tb.Focus()

    @property
    def find_name(self):
        return self.textbox.Text

    @property
    def replace_name(self):
        return self.textbox2.Text

    def rename_elements(self, sender, args):
        self.Close()
        # UI.TaskDialog.Show(
        #     "Batch Rename",
        #     'Replace "{}" with ({})'.format(self.find_name or '<blank>', self.replace_name or '<nothing>')
        #     )
logger = script.get_logger()

window = MyWindow()

all_graphviews = revit.query.get_all_views(doc=revit.doc)
# view_types = ['FloorPlan', 'CeilingPlan', 'Elevation', 'ThreeD', 'Section', 'Detail', 'Rendering']
# selected_views = forms.SelectFromList.show(
#                                 sorted([ViewOption(x) for x in all_graphviews],
#                                        key=lambda x: x.ViewType),
#                                 multiselect=True,
#                                 checked_only=True,
#                                 filterfunc=lambda x: x.ViewType.ToString() in view_types,
#                                 button_name='Select Views')

selected_views = forms.SelectFromList.show(
    {
        'All Views': [ViewOption(x) for x in all_graphviews],
        'Floor Plans': [ViewOption(x) for x in all_graphviews if x.ViewType.ToString() == 'FloorPlan'],
        # 'Ceiling Plans': [x.Name for x in all_graphviews if x.ViewType.ToString() == 'CeilingPlan'],
        'Elevations': [ViewOption(x) for x in all_graphviews if x.ViewType.ToString() == 'Elevation'],
        'ThreeD': [ViewOption(x) for x in all_graphviews if x.ViewType.ToString() == 'ThreeD'],
        # 'Sections': [x.Name for x in all_graphviews if x.ViewType.ToString() == 'Section'],
        # 'Details': [x.Name for x in all_graphviews if x.ViewType.ToString() == 'Detail'],
        # 'Renderings': [x.Name for x in all_graphviews if x.ViewType.ToString() == 'Rendering']

    },
    multiselect=True,
    checked_only=True,
    button_name='Select Views')

if selected_views:
    # let's show the window (modal)
    window.ShowDialog()
    old_text = window.find_name
    new_text = window.replace_name
    with revit.Transaction("Rename Views"): 
        for view in selected_views:
            try:
                if window.use_regex and window.use_ignorecase:
                    pattern = re.compile(old_text, re.IGNORECASE)
                    new_name = pattern.sub(new_text, view.Name)
                    view.Name = new_name
                elif window.use_regex:
                    pattern = re.compile(old_text)
                    new_name = pattern.sub(new_text, view.Name)
                    view.Name = new_name
                elif window.use_ignorecase:
                    pattern = re.compile(re.escape(old_text), re.IGNORECASE)
                    new_name = pattern.sub(new_text, view.Name)
                    view.Name = new_name
                else:
                    pattern = re.compile(re.escape(old_text))
                    new_name = pattern.sub(new_text, view.Name)
                    view.Name = new_name
            except ArgumentException:
                logger.warning("Unable to change name")

