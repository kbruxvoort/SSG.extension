from pyrevit import revit, DB
# from utils import check_revit_version

from parameters.shared import query_shared, get_shared_groups

app = revit.doc.Application
matched_params = query_shared(app, guid=['5e4dcf5a-efaa-40c4-bdcb-270318491ce5', '4a8f5927-12ae-43db-97df-4c815d37d809'])
# matched_params = query_shared(app, name='aCtUaL_', ptype=DB.SpecTypeId.Length)
# matched_params = query_shared(app, param_type=DB.SpecTypeId.Boolean.YesNo)


for definition in matched_params:
    print(definition.Name)