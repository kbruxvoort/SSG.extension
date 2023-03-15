from Autodesk.Revit.DB.ExtensibleStorage import Schema
    
if __name__ == "__main__":
    # fam = revit.pick_element(message='Pick a family')
    for s in Schema.ListSchemas():
        if s.ReadAccessGranted():
            print(s.SchemaName, s.VendorId)
            for f in s.ListFields():
                print("\t" + f.FieldName)