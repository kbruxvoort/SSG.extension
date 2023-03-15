# -*- coding: utf-8 -*-
# __title__ = "Template for my custom WPF windows."
# __author__ = "Erik Frits"

# ╦╔╦╗╔═╗╔═╗╦═╗╔╦╗╔═╗
# ║║║║╠═╝║ ║╠╦╝ ║ ╚═╗
# ╩╩ ╩╩  ╚═╝╩╚═ ╩ ╚═╝ IMPORTS
# ==================================================
#>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> .NET IMPORTS
import os, sys
from pyrevit import revit, forms

import os, clr
clr.AddReference("System")

import wpf
from System.Windows import Application, Window, ResourceDictionary
from System import Uri

# ╦ ╦╔═╗╔═╗  ╔╦╗╔═╗╔╦╗╔═╗╦  ╔═╗╔╦╗╔═╗
# ║║║╠═╝╠╣    ║ ║╣ ║║║╠═╝║  ╠═╣ ║ ║╣
# ╚╩╝╩  ╚     ╩ ╚═╝╩ ╩╩  ╩═╝╩ ╩ ╩ ╚═╝ WPF TEMPLATE
# ==================================================
class my_WPF(Window):
    def __init__(self, xaml_file):
        wpf.LoadComponent(self, xaml_file)

    def add_wpf_resource(self):
        """Function to add WPF resources."""
        dir_path        = os.path.dirname(__file__)
        path_styles     = os.path.join(dir_path, 'Resources/WPF_styles.xaml')
        r               = ResourceDictionary()
        r.Source        = Uri(path_styles)
        self.Resources  = r

    def show(self):
        self.ShowDialog()


