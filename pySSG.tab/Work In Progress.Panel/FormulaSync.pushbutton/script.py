from pyrevit import revit, DB


class FamilyLoadOptions(DB.IFamilyLoadOptions):
    def OnFamilyFound(self, familyInUse, overwriteParameterValues):
        overwriteParameterValues.Value = True
        return True


    def OnSharedFamilyFound(self, sharedFamily, familyInUse, source, overwriteParameterValues):
        source.Value = DB.FamilySource.Family
        overwriteParameterValues.Value = True
        return True
    
 
def isclose(a, b, rel_tol=1e-09, abs_tol=0.0):
    return abs(a-b) <= max(rel_tol * max(abs(a), abs(b)), abs_tol)  
  

def match_param(fam_inst, param_name):
    param = fam_inst.LookupParameter(param_name)
    if not param:
        param = fam_inst.Symbol.LookupParameter(param_name)
    return param


def get_param_value(param):
    if param.StorageType == DB.StorageType.Double:
        return param.AsDouble()
    elif param.StorageType == DB.StorageType.Integer:
        return param.AsInteger()
    elif param.StorageType == DB.StorageType.String:
        return param.AsString()
    elif param.StorageType == DB.StorageType.ElementId:
        return param.AsElementId()
    

sync_params = {
        "ACTUAL_Width": "if(Width < MIN_Width, MIN_Width, if(Width > MAX_Width, MAX_Width, zL00))",
        "ACTUAL_Depth": "if(Depth < MIN_Depth, MIN_Depth, if(Depth > MAX_Depth, MAX_Depth, zL01))",
        "ACTUAL_Height": "if(Height < MIN_Height, MIN_Height, if(Height > MAX_Height, MAX_Height, zL02))",
        "MAX_Width": 10,
        "MAX_Depth": 2.5,
        "MAX_Height": 3.416666666666667,
        "ADD_Locks": True,
        "ENTER_Handle Number": 5,
        "Width": 2.5
}

sel = revit.pick_element(message='Pick something dummy')

if sel:
    with revit.TransactionGroup("Sync Parameters"):
        with revit.Transaction("Update parameters"):
            fam = sel.Symbol.Family
            
            # looping through fake database dictionary
            for k,v in sync_params.items():
                project_param = match_param(sel, k)
                if project_param:
                    
                    # if it isn't determined by a formula do a normal parameter sync
                    if not project_param.IsReadOnly:
                        if project_param.StorageType == DB.StorageType.Double:
                            if not isclose(get_param_value(project_param), v, rel_tol=1e-04):
                                project_param.Set(v)
                                print("'{}' set to '{}'".format(k, v))
                            else:
                                print("'{}' is already good".format(k))
                        else:
                            if get_param_value(project_param) != v:
                                project_param.Set(v)
                                print("'{}' set to '{}'".format(k, v))
                            else:
                                print("'{}' is already good".format(k))
                                
                        # Remove synced parameters from list
                        sync_params.pop(k)
                        
        # Check if dictionary still has items. (Items that are read only)
        if sync_params:
            fam_doc = revit.doc.EditFamily(fam)
            fam_mgr = fam_doc.FamilyManager
            
            # family doesn't need to be loaded unless there is a discrepancy 
            needs_load = False
            for k,v in sync_params.items():
                
                # get parameter by name
                matched_param = fam_mgr.get_Parameter(k)
                if matched_param:
                    if matched_param.Formula != v:
                        
                        # there is a discrepancy so family will need to be loaded back into project after setting formula
                        needs_load = True
                        print("Change '{}' from '{}' to '{}'".format(k, matched_param.Formula, v))
                        
                        """ this transaction could be moved to the beginning of loop. 
                        Need to make sure it is happening in the family document and not the project"""
                        
                        with revit.Transaction(name='Update Formulas', doc=fam_doc):
                            fam_mgr.SetFormula(matched_param, v)
                        
            if needs_load:
                
                """ Might need to spend some time thinking through the load options. 
                I would default to False on all of these. It shouldn't affect the formula """
                
                fam = fam_doc.LoadFamily(revit.doc, FamilyLoadOptions())
            fam_doc.Close(False)