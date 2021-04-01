"""
This script allows the user to batch rename families. User has the option to use regular expressions and ignore case.
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

__title__ = " Batch rename families"
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
        

logger = script.get_logger()

window = MyWindow()

family_dict = {}
for family in revit.query.get_families(revit.doc, only_editable=True):
    if family.FamilyCategory:
        family_dict[
            "%s: %s" % (family.FamilyCategory.Name, family.Name)
            ] = family

if family_dict:
    selected_families = \
        forms.SelectFromList.show(
            sorted(family_dict.keys()),
            title="Select Families",
            multiselect=True)


if selected_families:
    # let's show the window (modal)
    window.ShowDialog()
    old_text = window.find_name
    new_text = window.replace_name
    with revit.Transaction("Rename Families"): 
        for idx, fam in enumerate([family_dict[x] for x in selected_families]):
            try:
                if window.use_regex and window.use_ignorecase:
                    pattern = re.compile(old_text, re.IGNORECASE)
                    new_name = pattern.sub(new_text, fam.Name)
                    fam.Name = new_name
                elif window.use_regex:
                    pattern = re.compile(old_text)
                    new_name = pattern.sub(new_text, fam.Name)
                    fam.Name = new_name
                elif window.use_ignorecase:
                    pattern = re.compile(re.escape(old_text), re.IGNORECASE)
                    new_name = pattern.sub(new_text, fam.Name)
                    fam.Name = new_name
                else:
                    pattern = re.compile(re.escape(old_text))
                    new_name = pattern.sub(new_text, fam.Name)
                    fam.Name = new_name
            except ArgumentException:
                logger.warning("Unable to change name")

