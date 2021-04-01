"""
This script allows the user to batch rename sheet names. User has the option to use regular expressions and ignore case.
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

__title__ = " Batch rename sheet names"
__author__ = "{{author}}"

class MyWindow(Windows.Window):
    def __init__(self):
        wpf.LoadComponent(self, xamlfile)

    @property
    def use_regex(self):
        return self.regexToggle.IsChecked

    @property
    def use_ignorecase(self):
        return self.caseToggle.IsChecked
    

    @property
    def find_name(self):
        return self.textbox.Text

    @property
    def replace_name(self):
        return self.textbox2.Text

    def rename_elements(self, sender, args):
        self.Close()

forms.check_modeldoc(revit.doc, exitscript=True)

logger = script.get_logger()

window = MyWindow()


selected_sheets = forms.select_sheets(button_name='Select Sheets')
if selected_sheets:
    # let's show the window (modal)
    window.ShowDialog()
    old_text = window.find_name
    new_text = window.replace_name
    with revit.Transaction("Rename Sheets"): 
        for sheet in selected_sheets:
            try:
                if window.use_regex and window.use_ignorecase:
                    pattern = re.compile(old_text, re.IGNORECASE)
                    new_name = pattern.sub(new_text, sheet.Name)
                    sheet.Name = new_name
                elif window.use_regex:
                    pattern = re.compile(old_text)
                    new_name = pattern.sub(new_text, sheet.Name)
                    sheet.Name = new_name
                elif window.use_ignorecase:
                    pattern = re.compile(re.escape(old_text), re.IGNORECASE)
                    new_name = pattern.sub(new_text, sheet.Name)
                    sheet.Name = new_name
                else:
                    pattern = re.compile(re.escape(old_text))
                    new_name = pattern.sub(new_text, sheet.Name)
                    sheet.Name = new_name
            except ArgumentException:
                logger.warning("Unable to change name")

