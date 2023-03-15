import json

import Autodesk.Revit.DB.ExtensibleStorage as es

from pyrevit import revit, script, forms, DB
from extensible_storage import HIDDEN_SCHEMA_GUID
from parameters import shared



# output = script.get_output()

app = revit.doc.Application

# make sure we can access shared parameters
definition_file = app.OpenSharedParameterFile()
if not definition_file:
    definition_file = shared.set_file(app)

# make sure exstensible storage schema exists
if definition_file:
    schema = es.Schema.Lookup(HIDDEN_SCHEMA_GUID)
    if not schema:
        # print("Making schema!")
        builder = es.SchemaBuilder(HIDDEN_SCHEMA_GUID)
        builder.SetReadAccessLevel(es.AccessLevel.Public)
        builder.SetWriteAccessLevel(es.AccessLevel.Public)
        builder.SetVendorId("pySSG")
        builder.SetSchemaName("HiddenParameters")
        builder.SetDocumentation(
            "This schema is used to map visible family parameters to a shared hidden parameter."
        )
        field_builder = builder.AddSimpleField("data", str)
        schema = builder.Finish()
    
    # check if there is an existing map
    entity = revit.doc.OwnerFamily.GetEntity(schema)
    value_dict = {}
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
        unable_swap = []
        type_dict = {}
        
        for sp in selected_params:
            associated_group = False
            # check if parameter is associated to group and can't be changed without ungrouping
            if sp.AssociatedParameters:
                for ap in sp.AssociatedParameters:
                    if ap.Element.GroupId:
                        associated_group = True
                        unable_swap.append(sp)
                        break
            if not associated_group:            
                if sp.Definition.ParameterType not in type_dict:
                    type_dict[sp.Definition.ParameterType] = []
                type_dict[sp.Definition.ParameterType].append(sp)
        
        # list of hidden parameters already in family for comparison
        existing_hidden = [fp for fp in revit.doc.FamilyManager.Parameters if not fp.Definition.Visible]    
        existing_hidden_names = [fp.Definition.Name for fp in existing_hidden]

        
        # get pySSG parameter group or create it if it doesn't exist
        group_name = "pySSG Hidden"
        def_group = definition_file.Groups.get_Item(group_name)
        if not def_group:
            def_group = definition_file.Groups.Create(group_name)
        
        # group existing hidden parameters into group by type
        ext_type_dict = {}
        for ed in def_group.Definitions:
            if not ed.Visible and ed.Name not in existing_hidden_names:
                if ed.ParameterType not in ext_type_dict:
                    ext_type_dict[ed.ParameterType] = []
                ext_type_dict[ed.ParameterType].append(ed)
                
        # loop through our grouped parameters
        with revit.Transaction("hide parameters"):           
            for k,v in type_dict.items():
                # print(k, [p.Definition.Name for p in v])
                # see if there are matching hidden parameters
                try:
                    sorted(ext_type_dict[k], key=lambda x: x.Name)
                except KeyError:
                    ext_type_dict[k] = []

                max_num = shared.extract_largest_index([d.Name for d in def_group.Definitions if d.ParameterType == k])
                for param in v:
                    # check if there are matching parameters. remove from list so we don't use it again.
                    if len(ext_type_dict[k]) > 0:
                        ext_def = ext_type_dict[k].pop()
                        # print("Using {} as a {} parameter".format(ext_def.Name,str(k)))
                    else:
                        # Create new parameter in pySSG group if not enough exist.
                        # print("Need to create a new {} ext def".format(str(k)))
                        # print(k)
                        # print(def_group)
                        # print(def_group.Definitions)
                        existing_params = [d.Name for d in def_group.Definitions if d.ParameterType == k]
                        # print(existing_params)
                        # param_index = shared.extract_largest_index([d.Name for d in def_group.Definitions if d.ParameterType == k])
                        new_name = "z" + str(k) + format(max_num + 1, '02d')
                        description = "Hidden {} type parameter".format(k)
                        # print("Creating parameter '{}'".format(new_name))
                        ext_def = shared.create_definition(
                            app, 
                            "pySSG Hidden",
                            new_name,
                            k,
                            description,
                            visible=False
                        )
                        max_num += 1
                        
                    group = param.Definition.ParameterGroup
                    original_name = param.Definition.Name
                    replaced_param = revit.doc.FamilyManager.ReplaceParameter(
                        param, 
                        ext_def, 
                        DB.BuiltInParameterGroup.INVALID, 
                        param.IsInstance
                    )
                    value_dict[original_name] = {
                        "ParameterGroup": str(group), 
                        "ParameterType": str(k),
                        "HiddenName": ext_def.Name, 
                        "HiddenGuid": str(ext_def.GUID)
                    }
            if value_dict:
                entity = es.Entity(schema)
                field = schema.GetField("data")
                entity.Set(field, json.dumps(value_dict))
                revit.doc.OwnerFamily.SetEntity(entity)
            if unable_swap:
                forms.alert(
                    "Unable to replace the following parameters because they are associated to groups: \n\n{}".format("\n".join([p.Definition.Name for p in unable_swap])),
                    title="Hide Parameters Warning",
                    sub_msg="Disassociate the parameters, use 'Hide' to replace with hidden, and then manually reassociate.",
                    cancel=True
                    )
