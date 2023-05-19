import os
import re


from pyrevit import revit, DB, script

from parameters import (
    STANDARD_PARAMETERS,
    PARAM_MAP,
    has_value,
    get_value,
    sort_parameter_into_group,
    is_built_in
)

BAD_EMOJI = ":cross_mark:"
# BAD_EMOJI = "BAD"
TACO_EMOJI = ":taco:"
# TACO_EMOJI = "TACO"
GOOD_EMOJI = ":white_heavy_check_mark:"
# GOOD_EMOJI = "GOOD"

def validate_string(pattern, input_string):
    regex = re.compile(pattern)
    match = regex.match(str(input_string))
    return bool(match)

def validate_family_name(family_name):
    pattern = r"^SSG_(([A-Z]|[A-Z][a-z]+|\d+)+_)+[A-Z]{3}"
    return validate_string(pattern, family_name)

def validate_type_name(family_name):
    pattern = r"^SSG_(([A-Z]|[A-Z][a-z]+|\d+)+_)+[A-Z]{3}"
    return validate_string(pattern, family_name)

def validate_nested_name(nested_name):
    pattern = r"^sub(_[a-z0-9]+)+"
    return validate_string(pattern, nested_name)

# validate OR param in standard names
def validate_parameter_name(parameter_name):
    pattern = r"(^([A-Z]+_)([A-Z]+[a-z]?\s?)+)|(z[A-Za-z]+\d*)"
    return validate_string(pattern, parameter_name) or parameter_name in STANDARD_PARAMETERS

def validate_manufacturer_value(parameter_value):
    pattern = r"^Southwest Solutions Group_[A-Z]{3}"
    return validate_string(pattern, parameter_value)

# def create_pattern_from_name(name):
#     # Replace group of words with a pattern that matches any character or whitespace
#     pattern = re.sub(r"(\b\w+\b\s*)+", r".+", name)
#     pattern = re.sub(r"\d+", r"\d+", pattern)
#     return pattern

def create_pattern_from_name(name):
    # Match patterns with one or more words separated by hyphens or other potential separators
    pattern = re.sub(r"([\w\s,]+)(?:\s*[-]\s*([\w\s,]+))+", r"([\w\s,]+(?:\s*[-]\s*[\w\s,]+)*)", name)
    pattern = re.sub(r"\d+", r"\d+", pattern)
    # pattern = re.escape(pattern)
    return pattern



def score_emoji(score):
    if score == 1.0:
        return TACO_EMOJI
    if score > .9:
        return GOOD_EMOJI
    return BAD_EMOJI


def test_family_name(family_document):
    if validate_family_name(family_document.Title):
        score = 1.0
        comments = ""
    else:
        score = 0.0
        comments = "{} did not pass name test".format(family_document.Title)
    return (score, comments)


def test_type_name(family_document):
    fam_mgr = family_document.FamilyManager
    current_type = fam_mgr.CurrentType
    types = [ft for ft in fam_mgr.Types if len(ft.Name) > 1]
    comments = ""
    if len(types) == 0:
        score = 0.0
        comments = "Only built-in type found"
    elif len(types) == 1:
        if types[0].Name == "Default":
            score = 1.0
        else:
            score = 0.0
            comments = "Single type should be named 'Default' not {}".format(types[0].Name)
    else:
        correct_count = 0
        comment_list = []
        pattern = create_pattern_from_name(current_type.Name)
        for ft in types:
            if validate_string(pattern, ft.Name):
                correct_count += 1
            else:
                comment_list.append("{} did not match pattern: {}".format(ft.Name, pattern))
        score = get_score(correct_count, len(types))
        # comments = "Multiple types need to be checked manually"
        comments = "<br>".join(comment_list)

    return (float(score), comments)


def test_param_names(family_document):
    param_names = [p.Definition.Name for p in family_document.FamilyManager.Parameters if not is_built_in(p)]
    count = 0
    comment_list = []
    if param_names:
        for pn in param_names:
            if validate_parameter_name(pn):
                count += 1
            else:
                comment_list.append(pn)
        score = get_score(count, len(param_names))
        comments = "<br>".join(comment_list)
    else:
        score = 1.0
        comments = "Only built-in parameters in family"
    return (score, comments)


def test_nested_names(family_document):
    nested_families = DB.FilteredElementCollector(family_document).OfClass(DB.Family).ToElements()
    nested_names = [nf.Name for nf in nested_families if nf.FamilyCategory.CategoryType == DB.CategoryType.Model and nf.Name]
    count = 0
    comment_list = []
    if nested_names:
        for nn in nested_names:
            if validate_nested_name(nn):
                count += 1
            else:
                comment_list.append(nn)
        score = get_score(count, len(nested_names))
        comments = "<br>".join(comment_list)
    else:
        score = 1.0
        comments = "No nested families found"
    return (score, comments)
        
    
def test_is_reference(family_document):
    ref_list = ["Left", "Center (Left/Right)", "Right", "Front", "Center (Front/Back)", "Back", "Bottom", "Center (Elevation)", "Top"]
    ref_planes = DB.FilteredElementCollector(family_document).OfClass(DB.ReferencePlane).ToElements()
    total = len(ref_list)
    for rp in ref_planes:
        is_ref_value = rp.get_Parameter(DB.BuiltInParameter.ELEM_REFERENCE_NAME).AsValueString()
        if is_ref_value in ref_list:
            ref_list.remove(is_ref_value)
    score = get_score(total - len(ref_list), total)
    if ref_list:
        ref_list.insert(0, "Missing IsReference:")
    comments = "<br>&emsp;".join(ref_list)
    return (score, comments)


def test_weak_reference(family_document):
    ref_planes = DB.FilteredElementCollector(family_document).OfClass(DB.ReferencePlane).ToElements()
    total = len(ref_planes)
    count = 0
    comment_list = []
    for rp in ref_planes:
        is_ref_value = rp.get_Parameter(DB.BuiltInParameter.ELEM_REFERENCE_NAME).AsValueString()
        if is_ref_value == "Weak Reference":
            if not rp.get_Parameter(DB.BuiltInParameter.DATUM_TEXT).AsValueString():
                count += 1
                comment_list.append(output.linkify(rp.Id))
    if count > 0:
        comment_list.insert(0, "{} weak references without a name".format(count))
    score = get_score(total - count, total)
    comments = "<br>".join(comment_list)
    return (score, comments)


def test_origin_reference(family_document):
    origin_list = ["Back", "Center (Left/Right)", "Bottom"]
    ref_planes = DB.FilteredElementCollector(family_document).OfClass(DB.ReferencePlane).ToElements()
    count = 0
    comment_list = []
    for rp in ref_planes:
        if rp.get_Parameter(DB.BuiltInParameter.DATUM_PLANE_DEFINES_ORIGIN).AsInteger() == 1:
            is_ref_value = rp.get_Parameter(DB.BuiltInParameter.ELEM_REFERENCE_NAME).AsValueString()
            if is_ref_value not in origin_list:
                count += 1
                comment_list.append("{}: {} should not define the origin".format(output.linkify(rp.Id), rp.get_Parameter(DB.BuiltInParameter.ELEM_REFERENCE_NAME).AsValueString()))
    score = get_score(len(origin_list) - count, len(origin_list))
    comments = "<br>".join(comment_list)
    return (score, comments)


def test_file_size(family_document):
    score = 1.0
    comments = ""
    doc_path = family_document.PathName
    if doc_path:
        file_size = os.path.getsize(doc_path)/1024
        comments = "{} KB".format(file_size)
        if file_size <= 1000:
            score = 1.0
        elif file_size > 2000:
            score = 0.0
        else:
            score = score - get_score(float(file_size - 1000), 1000)
    else:
        comments = "Unable to get file size. Save family locally"
    return (score, comments)


def test_file_category(family_document):
    approved_categories_ids = [
        family_document.Settings.Categories.get_Item(DB.BuiltInCategory.OST_Casework).Id, 
        family_document.Settings.Categories.get_Item(DB.BuiltInCategory.OST_Furniture).Id, 
        family_document.Settings.Categories.get_Item(DB.BuiltInCategory.OST_FurnitureSystems).Id,
        family_document.Settings.Categories.get_Item(DB.BuiltInCategory.OST_LightingFixtures).Id,
        family_document.Settings.Categories.get_Item(DB.BuiltInCategory.OST_PlumbingFixtures).Id,
        family_document.Settings.Categories.get_Item(DB.BuiltInCategory.OST_SecurityDevices).Id,
        family_document.Settings.Categories.get_Item(DB.BuiltInCategory.OST_SpecialityEquipment).Id
    ]
    score = 1.0
    comments = ""
    category = family_document.OwnerFamily.FamilyCategory
    if category.Id not in approved_categories_ids:
        score = 0.0
        comments = "{} is not an approved category".format(category.Name)
    return (score, comments)


def test_plan_geometry(family_document):
    model_elements = DB.FilteredElementCollector(family_document, family_document.ActiveView.Id).OfClass(DB.GenericForm).ToElements()
    score = 1.0
    if model_elements:
        count = 0
        comment_list = []
        for m in model_elements:
            visibility = m.GetVisibility()
            if visibility.IsShownInTopBottom:
                count += 1
                comment_list.append(output.linkify(m.Id))
        comments = "<br>".join(comment_list)
        score = get_score(len(model_elements) - score, len(model_elements))
    else:
        comments = "No geometry in plan."
    return (score, comments)

def test_plan_lod(family_document):
    model_elements = DB.FilteredElementCollector(family_document, family_document.ActiveView.Id).OfClass(DB.GenericForm).ToElements()
    nested_instances = DB.FilteredElementCollector(family_document, family_document.ActiveView.Id).OfClass(DB.FamilyInstance).ToElements()
    comments = ""
    geo_has_detail = False
    if model_elements:
        for m in model_elements:
            visibility = m.GetVisibility()
            if not(visibility.IsShownInCoarse or visibility.IsShownInMedium):
                score = 1.0
                geo_has_detail = True
                break
    inst_has_detail = False
    for instance in nested_instances:
        visibility_param = instance.get_Parameter(DB.BuiltInParameter.GEOM_VISIBILITY_PARAM)
        if visibility_param:
            visibility = visibility_param.AsInteger()
            if visibility < 50000:
                inst_has_detail = True
    
    score = float(int(geo_has_detail or inst_has_detail))
    if score < 1.0:
        comments = "No changes in detail level found"
    return (score, comments)
            

def test_standard_params(family_document):
    total = len(STANDARD_PARAMETERS)
    parameters = [p for p in family_document.FamilyManager.Parameters if not is_built_in(p)]
    for p in parameters:
        if p.Definition.Name in STANDARD_PARAMETERS:
            STANDARD_PARAMETERS.pop(p.Definition.Name)
    score = get_score(total - len(STANDARD_PARAMETERS), total)
    comments = "<br>".join(STANDARD_PARAMETERS.keys())
    return (score, comments)


def test_param_group(family_document):
    parameters = [p for p in family_document.FamilyManager.Parameters if not is_built_in(p)]
    comment_list = []
    count = 0
    score = 1.0
    comments = ""
    if parameters:
        for p in parameters:
            original_group = p.Definition.ParameterGroup
            correct_group = sort_parameter_into_group(p, PARAM_MAP)
            if original_group == correct_group:
                count += 1
            else:
                comment_list.append("{}: {} should be {}".format(p.Definition.Name, str(original_group), str(correct_group)))
        score = get_score(count, len(parameters))
        comments = "<br>".join(comment_list)
        
    return (score, comments)


def test_param_values(family_document):
    fam_mgr = family_document.FamilyManager
    current_type = fam_mgr.CurrentType
    other_param_names = [
        "URL_Contact Fetch",
        "SSG_Toll Free Number",
        "URL_Product Page",
        "URL_Specification Manual"
    ]
    comment_list = []
    
    parameters = [p for p in fam_mgr.Parameters if not is_built_in(p) and p.Definition.Name not in other_param_names]
    other_parameters = [p for p in fam_mgr.Parameters if p.Definition.Name in other_param_names]
    
    # BuiltIn values
    mfr_param = fam_mgr.get_Parameter(DB.BuiltInParameter.ALL_MODEL_MANUFACTURER)
    mfr_value = get_value(mfr_param, current_type)
    mfr_score = int(validate_manufacturer_value(mfr_value))
    if mfr_score < 1:
        comment_list.append(mfr_param.Definition.Name)
    
    keynote_param = fam_mgr.get_Parameter(DB.BuiltInParameter.KEYNOTE_PARAM)
    keynote_score = int(has_value(keynote_param, current_type))
    if keynote_score < 1:
        comment_list.append(keynote_param.Definition.Name)
    
    assem_param = fam_mgr.get_Parameter(DB.BuiltInParameter.UNIFORMAT_CODE)
    assem_score = int(has_value(assem_param, current_type))
    if assem_score < 1:
        comment_list.append(assem_param.Definition.Name)
    
    url_param = fam_mgr.get_Parameter(DB.BuiltInParameter.ALL_MODEL_URL)
    url_value = get_value(url_param, current_type)
    url_score = int(url_value == "https://fetchbim.com")
    if url_score < 1:
        comment_list.append(url_param.Definition.Name)
    
    omni_param = family_document.OwnerFamily.get_Parameter(DB.BuiltInParameter.OMNICLASS_CODE)
    omni_score = int(bool(omni_param.AsString()))
    if omni_score < 1:
        comment_list.append(omni_param.Definition.Name)
        
    # Specific values
    # Has Formula or Has Value unless it's builtin. Will need to filter out 
    others_score = 0
    for p in parameters:
        if has_value(p, current_type):
            others_score += 1
        else:
            comment_list.append(p.Definition.Name)    
    
    score = float(mfr_score + keynote_score + assem_score + url_score + omni_score + others_score) / (5 + len(parameters))
    comments = "<br>".join(comment_list)
    return (float(score), comments)


def run_tests(family_document):
    results = []
    for group, name, test_func in tests:
        result, comments = test_func(family_document)
        emoji = score_emoji(result)
        results.append((group, name, comments, result, emoji))
    total_score = score_average([r[3] for r in results])
    total = ["Total", "", "", total_score, score_emoji(total_score)]
    results.append(total)
    return results

def get_score(numerator, denominator):
    try:
        return float(numerator) / float(denominator)
    except ZeroDivisionError:
        return 0.0
    
def score_average(score_list):
    return float(sum(score_list)) / len(score_list)

def create_health_chart(test_table):
    grouped_dict = {}
    for row in test_table:
        group = row[0]
        score = row[3]
        if group not in grouped_dict:
            grouped_dict[group] = []
        grouped_dict[group].append(score)
    if grouped_dict:
        labels, data = [], []    
        for k,v in grouped_dict.items():
            labels.append(k)
            data.append(score_average(v))
        chart = output.make_radar_chart()
        chart.options.scale = {"ticks": {"min": 0, "max": 1}}
        chart.options.tooltips = {'enabled': True,
                                  'intersect': True,
                                  'backgroundColor': 'rgba(0,0,0,0.8)',
                                  'caretSize': 5,
                                  'displayColors': True}
        chart.options.legend = {'display': False}
        chart.data.labels = labels
        set = chart.data.new_dataset('Health Score')
        set.data = data
        set.set_color(39, 149, 192, .5)
        chart.draw()


output = script.get_output()
output.resize(900, 900)
# output.set_font(font_family="Segoe UI Emoji", font_size=16)


tests = [
    ("Name", "Family Name", test_family_name),
    ("Name", "Type Name", test_type_name),
    ("Name", "Parameter Names", test_param_names),
    ("Name", "Nested Names", test_nested_names),
    ("References", "IsReferences", test_is_reference),
    ("References", "Weak References", test_weak_reference),
    ("References", "Origin References", test_origin_reference),
    ("File", "File Size", test_file_size),
    ("File", "File Category", test_file_category),
    ("Plan View", "Hidden Geometry", test_plan_geometry),
    ("Plan View", "Level of Detail", test_plan_lod),
    ("Parameters", "Standard Parameters", test_standard_params),
    ("Parameters", "Parameter Groups", test_param_group),
    ("Parameters", "Parameter Values", test_param_values),
]

table = run_tests(revit.doc)
create_health_chart(table[:-1])
columns = ['Group', 'Item', 'Issues', 'Score', 'emoji']

output.print_table(
    table_data=table,
    columns=columns,
    formats=['', '', '', '<strong>{:.0%}', ''],
    last_line_style='font-size: 16px; font-weight: 700'
)
