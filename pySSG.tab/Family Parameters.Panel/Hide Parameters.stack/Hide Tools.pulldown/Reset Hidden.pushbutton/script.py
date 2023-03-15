import json
from System import Guid
import Autodesk.Revit.DB.ExtensibleStorage as es

from pyrevit import revit, DB, forms
from extensible_storage import HIDDEN_SCHEMA_GUID



schema = es.Schema.Lookup(HIDDEN_SCHEMA_GUID)
if schema:
    entity = revit.doc.OwnerFamily.GetEntity(schema)
    if entity.IsValid():
        value_string = entity.Get[str]("data")
        value_dict = json.loads(value_string)
        if value_dict:
            with revit.Transaction("Reset hidden parameters"):
                unable_swap = []
                for k,v in value_dict.items():
                    associated_group = False
                    fam_mgr = revit.doc.FamilyManager
                    group_enum = getattr(DB.BuiltInParameterGroup, v["ParameterGroup"])
                    param = fam_mgr.get_Parameter(Guid(v["HiddenGuid"]))
                    if param:
                        if param.AssociatedParameters:
                            for ap in param.AssociatedParameters:
                                if ap.Element.GroupId:
                                    associated_group = True
                                    unable_swap.append(param)
                                    break
                        if not associated_group:
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