import json

import Autodesk.Revit.DB.ExtensibleStorage as es

from pyrevit import revit, script, forms, DB
from extensible_storage import HIDDEN_SCHEMA_GUID, create_hidden_param_schema
from parameters import (
    SharedParameterFile, 
    get_array_original_element_ids, 
    param_associated_to_array,
    save_param_order
)


def get_available_shared_parameter_name(param_type, excluded_names):
    for i in range(100):
        name = 'z{}{:02d}'.format(param_type.ToString(), i)
        if name not in excluded_names:
            return name
    return None

def get_shared_parameter(parameter_name, parameter_type, shared_parameter_file):
    ext_df = shared_parameter_file.query(name=parameter_name, first_only=True)
    if not ext_df:
        ext_df = shared_parameter_file.create_definition(
            group_name="pySSG Hidden", 
            name=parameter_name, 
            parameter_type=parameter_type, 
            description="Hidden {} type parameter".format(str(parameter_type)), 
            guid=None, 
            hide_no_value=False,
            visible=False
        )
    return ext_df


# make sure we can access shared parameters
definition_file = SharedParameterFile()

# make sure exstensible storage schema exists
if definition_file:
    schema = es.Schema.Lookup(HIDDEN_SCHEMA_GUID)
    if not schema:
        schema = create_hidden_param_schema()
    
    # check if there is an existing map
    entity = revit.doc.OwnerFamily.GetEntity(schema)
    value_dict = {
        "map": {},
        "sort": {}
    }
    if entity.IsValid():
        value_string = entity.Get[str]("data")
        value_dict = json.loads(value_string)
    
    # user selects parameters to hide (builtin and inivisble parameters are filtered out)    
    selected_params = forms.select_family_parameters(
        revit.doc,
        title='Select Parameters to Hide', 
        filterfunc=lambda x: x.Definition.Visible, 
        include_builtin=False
    )
    
    # group parameters to be swapped into group by type
    if selected_params:
        # list of hidden parameters already in family for comparison
        existing_hidden = [fp for fp in revit.doc.FamilyManager.Parameters if not fp.Definition.Visible]    
        existing_hidden_names = [fp.Definition.Name for fp in existing_hidden]
        
        unable_swap = []
        type_dict = {}
        
        array_element_ids = get_array_original_element_ids(revit.doc)
        count = 0
        value_dict["sort"] = save_param_order(revit.doc)
        with revit.Transaction("hide parameters"):
            for sp in selected_params:
                
                # skip parameters that can't be changed because they are in an array
                associated_array = param_associated_to_array(sp, array_element_ids)
                if associated_array:
                    unable_swap.append(sp)
                else:
                    name = get_available_shared_parameter_name(sp.Definition.ParameterType, existing_hidden_names)
                    ext_def = get_shared_parameter(name, sp.Definition.ParameterType, definition_file)
                    group = sp.Definition.ParameterGroup
                    original_name = sp.Definition.Name
                    original_type = sp.Definition.ParameterType
                    is_shared = sp.IsShared
                    if is_shared:
                        original_guid = sp.GUID
                    else:
                        original_guid = None
                    replaced_param = revit.doc.FamilyManager.ReplaceParameter(
                        sp, 
                        ext_def, 
                        DB.BuiltInParameterGroup.INVALID, 
                        sp.IsInstance
                    )
                    existing_hidden_names.append(name)
                    value_dict["map"][original_name] = {
                        "ParameterGroup": str(group), 
                        "ParameterType": str(original_type),
                        "HiddenName": ext_def.Name, 
                        "HiddenGuid": str(ext_def.GUID),
                        "IsShared": is_shared,
                        "SharedGuid": str(original_guid)
                    }
                    count+= 1
                    
            # successful count
            forms.alert(
                    msg="Successfully hid {} parameters".format(count),
                    warn_icon=False
                )
            
            # set extensible storage
            if value_dict:
                entity = es.Entity(schema)
                field = schema.GetField("data")
                entity.Set(field, json.dumps(value_dict))
                revit.doc.OwnerFamily.SetEntity(entity)
            
            # alert about unswappable parameters    
            if unable_swap:
                forms.alert(
                    "Unable to replace the following parameters because they are associated to groups: \n\n{}".format("\n".join([p.Definition.Name for p in unable_swap])),
                    title="Hide Parameters Warning",
                    sub_msg="Disassociate the parameters, use 'Hide' to replace with hidden, and then manually reassociate.",
                    cancel=True
                    )

                        
                    
                    
            
