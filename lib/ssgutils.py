from math import floor
from pyrevit import DB


def is_float(value):
    try:
        float(value)
        return True
    except ValueError:
        return False


def max_sheet_num(sheet_list):
    max_num = max(
        floor(float(s.SheetNumber)) for s in sheet_list if is_float(s.SheetNumber)
    )
    if max_num:
        return max_num
    else:
        return 0


def get_rectangle(view):
    oLine = view.Outline
    minU = oLine.Min.U
    minV = oLine.Min.V
    maxU = oLine.Max.U
    maxV = oLine.Max.V

    # get width and length of Rectangle
    w = maxU - minU
    l = maxV - minV

    return (w, l)


def list_to_dict(e_list, attr="Name"):
    ele_list, properties = [], []
    for l in e_list:
        ele_list.append(l)
        try:
            properties.append(getattr(l, attr))
        except:
            properties.append(DB.Element.Name.__get__(l))

    d1 = zip(properties, ele_list)
    return dict(d1)


def list_to_dict_2(e_list):
    ele_list, properties = [], []
    for l in e_list:
        ele_list.append(l)
        properties.append("{}: {}".format(l.FamilyName, DB.Element.Name.__get__(l)))

    d1 = zip(properties, ele_list)
    return dict(d1)
