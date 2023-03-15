from pyrevit import revit, DB

from Autodesk.Revit import Exceptions

class FamilyLoadOptions(DB.IFamilyLoadOptions):
    def OnFamilyFound(self, familyInUse, overwriteParameterValues):
        overwriteParameterValues.Value = True
        return True


    def OnSharedFamilyFound(self, sharedFamily, familyInUse, source, overwriteParameterValues):
        source.Value = DB.FamilySource.Family
        overwriteParameterValues.Value = True
        return True

fam_inst = revit.selection.pick_element()

fam_doc = revit.doc.EditFamily(fam_inst.Symbol.Family)

value = 'Width / 2'
fam_manager = fam_doc.FamilyManager
params = fam_manager.GetParameters()
fam_params = [p for p in params if p.Definition.Name == 'Depth']
# print(fam_params[0].Definition.Name)

with revit.Transaction(doc=fam_doc, name='Set Family Parameter Formula'):
    try:
        fam_manager.SetFormula(fam_params[0], value)
    except Exceptions.ArgumentException as e:
        print(e)

fam_doc.LoadFamily(revit.doc, FamilyLoadOptions())