import json
from System import Guid
from System.Collections.Generic import List
import Autodesk.Revit.DB.ExtensibleStorage as es

from pyrevit import revit, DB, forms
from extensible_storage import HIDDEN_SCHEMA_GUID
from parameters import get_array_original_element_ids, param_associated_to_array, SharedParameterFile



schema = es.Schema.Lookup(HIDDEN_SCHEMA_GUID)
if schema:
    entity = revit.doc.OwnerFamily.GetEntity(schema)
    if entity.IsValid():
        value_string = entity.Get[str]("data")
        value_dict = json.loads(value_string)
        if value_dict:
            array_element_ids = get_array_original_element_ids(revit.doc)
            fam_mgr = revit.doc.FamilyManager
            spf = SharedParameterFile()
            with revit.TransactionGroup("Reset hidden parameters"):
                with revit.Transaction("Reset hidden parameters"):
                    count = 0
                    unable_swap = []
                    for k,v in value_dict["map"].items():
                        associated_group = False
                        group_enum = getattr(DB.BuiltInParameterGroup, v["ParameterGroup"])
                        param = fam_mgr.get_Parameter(Guid(v["HiddenGuid"]))
                        if param:
                            associated_array = param_associated_to_array(param, array_element_ids)
                            if associated_array:
                                unable_swap.append(param)

                            else:
                                replaced_param = None
                                if v["IsShared"] is True:
                                    new_param = spf.query(guid=v["SharedGuid"], first_only=True)

                                    if new_param:
                                        replaced_param = fam_mgr.ReplaceParameter(
                                            param,
                                            new_param,
                                            group_enum,
                                            param.IsInstance
                                        )

                                if not replaced_param:    
                                    fam_mgr.ReplaceParameter(
                                        param,
                                        k,
                                        group_enum,
                                        param.IsInstance
                                    )
                                count += 1
                    if unable_swap:
                        forms.alert(
                            "Unable to replace the following parameters because they are associated to groups: \n\n{}".format("\n".join([p.Definition.Name for p in unable_swap])),
                            title="Reset Hidden Parameters Warning",
                            sub_msg="Disassociate the parameters, use 'Reset Hidden' to replace hidden with original parameter, and then manually reassociate.",
                            cancel=True
                            )
                    param_list = List[DB.FamilyParameter]()
                    for p in sorted(fam_mgr.GetParameters(), key=lambda x: value_dict["sort"].get(x.Definition.Name, -1)):
                        param_list.Add(p)
                            
                    fam_mgr.ReorderParameters(param_list)
                
                with revit.Transaction("Clear extensible storage"):
                    emptied_dict = {"sort": {}, "map": {}}
                    field = schema.GetField("data")
                    entity.Set(field, json.dumps(emptied_dict))
                    revit.doc.OwnerFamily.SetEntity(entity)
                    
                forms.alert(
                    msg="Successfully reset {} hidden parameters".format(count),
                    warn_icon=False
                )
