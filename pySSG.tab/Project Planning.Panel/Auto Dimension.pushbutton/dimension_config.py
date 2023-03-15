"""Activates selection tool that picks a specific type of element.

Shift-Click:
Pick favorites from all available categories
"""
# pylint: disable=E0401,W0703,C0103
from pyrevit import revit, DB
from pyrevit import forms
from pyrevit import script


logger = script.get_logger()
my_config = script.get_config("dim_categories")


# somehow DB.BuiltInCategory.OST_Truss does not have a corresponding DB.Category
FREQUENTLY_SELECTED_CATEGORIES = [
    DB.BuiltInCategory.OST_Casework,
    DB.BuiltInCategory.OST_Furniture,
    DB.BuiltInCategory.OST_FurnitureSystems,
    DB.BuiltInCategory.OST_SpecialityEquipment
]


class FSCategoryItem(forms.TemplateListItem):
    """Wrapper class for frequently selected category list item"""
    pass


def load_configs():
    """Load list of frequently selected categories from configs or defaults"""
    dim_cats = my_config.get_option('dim_cats', [])
    revit_cats = [revit.query.get_category(x)
                  for x in (dim_cats or FREQUENTLY_SELECTED_CATEGORIES)]
    return filter(None, revit_cats)


def save_configs(categories):
    """Save given list of categories as frequently selected"""
    my_config.dim_cats = [x.Name for x in categories]
    script.save_config()


def reset_defaults(options):
    """Reset frequently selected categories to defaults"""
    defaults = [revit.query.get_category(x)
                for x in FREQUENTLY_SELECTED_CATEGORIES]
    default_names = [x.Name for x in defaults if x]
    for opt in options:
        if opt.name in default_names:
            opt.checked = True


def configure_dim_cats():
    """Ask for users frequently selected categories"""
    prev_dim_cats = load_configs()
    all_cats = revit.doc.Settings.Categories
    prev_dim_cats = [x.Name for x in prev_dim_cats]
    dim_cats = forms.SelectFromList.show(
        sorted(
            [FSCategoryItem(x,
                            checked=x.Name in prev_dim_cats,
                            name_attr='Name')
             for x in all_cats],
            key=lambda x: x.name
            ),
        title='Select Favorite Categories',
        button_name='Apply',
        multiselect=True,
        resetfunc=reset_defaults
    )
    if dim_cats:
        save_configs(dim_cats)
    return dim_cats


if __name__ == "__main__":
    configure_dim_cats()
