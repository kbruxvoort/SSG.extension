from .family import *
from .shared import *


def get_array_original_element_ids(family_document):
    arrays = DB.FilteredElementCollector(family_document).OfCategory(DB.BuiltInCategory.OST_IOSArrays).ToElements()
    array_element_ids = []
    for a in arrays:
        array_element_ids.extend(a.GetOriginalMemberIds())
    return array_element_ids

def param_associated_to_array(parameter, array_element_ids):
    if parameter.AssociatedParameters:
        for ap in parameter.AssociatedParameters:
            if ap.Element.GroupId in array_element_ids:
                return True
    return False