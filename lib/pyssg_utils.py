from pyrevit import HOST_APP

def check_revit_version():
    print(HOST_APP.version)
    print(HOST_APP.build)
    print(HOST_APP.is_newer_than(2019))
    print(HOST_APP.is_older_than(2019))
    
def isclose(a, b, rel_tol=1e-09, abs_tol=0.0):
    return abs(a-b) <= max(rel_tol * max(abs(a), abs(b)), abs_tol)

def to_list(lst):
    if not isinstance(lst, list):
        lst = [lst]
    return lst

def int_to_rgb(color_int):
    red = ((color_int >> 16) & 0xFF) / 255.0
    green = ((color_int >> 8) & 0xFF) / 255.0
    blue = (color_int & 0xFF) / 255.0
    return (red, green, blue)

def rgb_to_int(rgb):
    red = int(rgb[0] * 255)
    green = int(rgb[1] * 255)
    blue = int(rgb[2] * 255)
    return (red << 16) | (green << 8) | blue