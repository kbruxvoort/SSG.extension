__persistentengine__ = True
# __min_revit_ver__= 2019

from pyrevit import HOST_APP, DB
from System import Guid
from Autodesk.Revit.UI import TaskDialog

class ExampleUpdater(DB.IUpdater):

    def __init__(self, addin_id):
        self.id = DB.UpdaterId(addin_id, Guid("70f3be2d-b524-4798-8baf-5b249c2f31c4"))
        self.TaskDialog = TaskDialog

    def GetUpdaterId(self):
        return self.id

    def GetUpdaterName(self):
        return "Example Updater"

    def GetAdditionalInformation(self):
        return "Just an example"

    def GetChangePriority(self):
        return DB.ChangePriority.Views

    def Execute(self, data):
        doc = data.GetDocument()
        
        for id in data.GetModifiedElementIds():
            wall = doc.GetElement(id)
            try:
                self.do_thing(wall)

            except Exception as err:
                # wall.ParametersMap["Comments"].Set("{}: {}".format(err.__class__.__name__, err))
                p = wall.get_Parameter(DB.BuiltInParameter.ALL_MODEL_COMMENTS)
                p.Set("Fuck")
    
    def do_thing(self, wall):
        self.TaskDialog.Show('ExampleUpdater', 'Updating {}'.format(wall.Id.IntegerValue))