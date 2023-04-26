import json
from System import Guid
from System.Collections.Generic import List
import Autodesk.Revit.DB.ExtensibleStorage as es

from pyrevit import revit, DB, forms
from extensible_storage import HIDDEN_SCHEMA_GUID
from parameters import get_array_original_element_ids, param_associated_to_array



schema = es.Schema.Lookup(HIDDEN_SCHEMA_GUID)
if schema:
    entity = revit.doc.OwnerFamily.GetEntity(schema)
    if entity.IsValid():
        value_string = entity.Get[str]("data")
        value_dict = json.loads(value_string)
        if value_dict:
            array_element_ids = get_array_original_element_ids(revit.doc)
            fam_mgr = revit.doc.FamilyManager
            with revit.Transaction("Reset hidden parameters"):
                unable_swap = []
                for k,v in value_dict["map"].items():
                    associated_group = False
                    
                    group_enum = getattr(DB.BuiltInParameterGroup, v["ParameterGroup"])
                    param = fam_mgr.get_Parameter(Guid(v["HiddenGuid"]))
                    if param:
                        associated_array = param_associated_to_array(param, array_element_ids)
                        if associated_array:
                            unable_swap.append(param)
                        # if param.AssociatedParameters:
                        #     for ap in param.AssociatedParameters:
                        #         if ap.Element.GroupId:
                        #             associated_group = True
                        #             unable_swap.append(param)
                        #             break
                        # if not associated_group:
                        else:
                            revit.doc.FamilyManager.ReplaceParameter(
                                param,
                                k,
                                group_enum,
                                param.IsInstance
                            )
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