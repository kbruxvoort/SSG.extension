import os, sys
from pyrevit import script

import os, clr
clr.AddReference("System")

import wpf
from System.Windows import Application, Window, ResourceDictionary
from System import Uri,UriKind


class BaseWPF(Window):
    def __init__(self, xaml_filename):
        wpf.LoadComponent(self, script.get_bundle_file(xaml_filename))
        style_xaml = os.path.join(os.path.dirname(__file__), "Styles.xaml")
        Application.LoadComponent(self, Uri(style_xaml, UriKind.Relative))

    # def add_wpf_resource(self):
    #     """Function to add WPF resources."""
    #     dir_path        = os.path.dirname(__file__)
    #     path_styles     = os.path.join(dir_path, 'Resources/Styles.xaml')
    #     r               = ResourceDictionary()
    #     r.Source        = Uri(path_styles)
    #     self.Resources  = r

    def show(self):
        self.ShowDialog()


