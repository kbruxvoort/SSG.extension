import re

from System import Guid
from Autodesk.Revit.Exceptions import InvalidOperationException, ArgumentNullException, ArgumentOutOfRangeException, ArgumentException

from pyrevit import revit, DB, HOST_APP
from pyrevit.framework import Forms

from pyssg_utils import to_list


STANDARD_PARAMETERS = {
    "STD_Widths": DB.BuiltInParameterGroup.PG_CONSTRAINTS,
    "MIN_Width": DB.BuiltInParameterGroup.PG_CONSTRAINTS,
    "MAX_Width": DB.BuiltInParameterGroup.PG_CONSTRAINTS,
    "STD_Depths": DB.BuiltInParameterGroup.PG_CONSTRAINTS,
    "MIN_Depth": DB.BuiltInParameterGroup.PG_CONSTRAINTS,
    "MAX_Depth": DB.BuiltInParameterGroup.PG_CONSTRAINTS,
    "STD_Heights": DB.BuiltInParameterGroup.PG_CONSTRAINTS,
    "MIN_Height": DB.BuiltInParameterGroup.PG_CONSTRAINTS,
    "MAX_Height": DB.BuiltInParameterGroup.PG_CONSTRAINTS,
    "INFO_Lead Time": DB.BuiltInParameterGroup.PG_CONSTRUCTION,
    "URL_Finish Options": DB.BuiltInParameterGroup.PG_IDENTITY_DATA,
    "ACTUAL_Weight": DB.BuiltInParameterGroup.PG_STRUCTURAL,
    "ACTUAL_Width": DB.BuiltInParameterGroup.PG_GEOMETRY,
    "ACTUAL_Depth": DB.BuiltInParameterGroup.PG_GEOMETRY,
    "ACTUAL_Height": DB.BuiltInParameterGroup.PG_GEOMETRY,
    # "URL_Sustainability": DB.BuiltInParameterGroup.PG_GREEN_BUILDING,
    "TOTAL_List Price": DB.BuiltInParameterGroup.PG_DATA,
    "zM": DB.BuiltInParameterGroup.INVALID,
    # "zO": DB.BuiltInParameterGroup.INVALID,
    "zP": DB.BuiltInParameterGroup.INVALID,
    "SSGFID": DB.BuiltInParameterGroup.PG_IDENTITY_DATA,
    "SSGTID": DB.BuiltInParameterGroup.PG_IDENTITY_DATA,
    "SSG_Author": DB.BuiltInParameterGroup.PG_IDENTITY_DATA,
    "SSG_Product Code": DB.BuiltInParameterGroup.PG_IDENTITY_DATA,
    "SSG_Toll Free Number": DB.BuiltInParameterGroup.PG_IDENTITY_DATA,
    "URL_Contact Fetch": DB.BuiltInParameterGroup.PG_IDENTITY_DATA,
    # "URL_Installation Manual": DB.BuiltInParameterGroup.PG_IDENTITY_DATA,
    "URL_Product Page": DB.BuiltInParameterGroup.PG_IDENTITY_DATA,
    # "URL_Specification Manual": DB.BuiltInParameterGroup.PG_IDENTITY_DATA,
}

class SharedParameterFile:
    def __init__(self, file_path=None):
        self.file_path = file_path
        self.file = None
        
        if not self.file_path:
            current_file = HOST_APP.app.OpenSharedParameterFile()
            if current_file:
                self.file_path = current_file.Filename
                self.file = current_file
                       
        if self.file_path and not self.file:
            HOST_APP.app.SharedParametersFilename = self.file_path
            self.file = HOST_APP.app.OpenSharedParameterFile()
            
        if not self.file:
            selected_path = None
            dialog = Forms.OpenFileDialog()
            dialog.Title = "Select an External Definition File"
            dialog.Filter = "Text Files (*.txt)|*.txt|All Files (*.*)|*.*"
            if dialog.ShowDialog() == Forms.DialogResult.OK:
                selected_path = dialog.FileName
            else:
                raise Exception("No External Definition File selected.")
            
            self.file_path = selected_path
            HOST_APP.app.SharedParametersFilename = selected_path
            self.file = HOST_APP.app.OpenSharedParameterFile()
    
    def set_file(self, file_path=None):
        if not file_path:
            dialog = Forms.OpenFileDialog()
            dialog.Title = "Select an External Definition File"
            dialog.Filter = "Text Files (*.txt)|*.txt|All Files (*.*)|*.*"
            if dialog.ShowDialog() == Forms.DialogResult.OK:
                file_path = dialog.FileName
            else:
                raise Exception("No External Definition File selected.")
        
        self.file_path = file_path
        HOST_APP.app.SharedParametersFilename = file_path
        self.file = HOST_APP.app.OpenSharedParameterFile()
    
    
    def get_file(self):
        print(self.file)
        
    
    def list_definitions(self):
        return sorted([definition for group in self.file.Groups for definition in group.Definitions], key=lambda d: (d.OwnerGroup, d.Name))

        
    def find_group_by_name(self, group_name):
        return self.file.Groups.get_Item(group_name)
    
        
    def find_shared_by_name(self, group_name, definiton_name):
        group = self.find_group_by_name(group_name)
        if group:
            definition = group.Definitions.get_Item(definiton_name)
            return definition
        
        
    def query(self, group_name=None, guid=None, name=None, param_type=None, hidden=None, first_only=False):
        definitions = []
        if group_name:
            groups = self.file.Groups
            group_name = to_list(group_name)
            for gn in group_name:
                group = groups.get_Item(gn)
                definitions.extend(group.Definitions)
        else:
            definitions = self.list_definitions()
            
        if guid:
            guid = to_list(guid)
            definitions = [d for d in definitions if any(d.GUID.ToString() == g for g in guid)]
            
        if name:
            name = to_list(name)
            definitions = [d for d in definitions if any(n.lower() in d.Name.lower() for n in name)]
            
        if param_type:
            if HOST_APP.is_newer_than(2020):
                definitions = filter(lambda x: x.GetDataType() == param_type, definitions)
            else:
                definitions = filter(lambda x: x.ParameterType == param_type, definitions)
                
        if hidden is True:
            definitions = filter(lambda x: x.Visible == False, definitions)
        elif hidden is False:
            definitions = filter(lambda x: x.Visible == True, definitions)
                  
        if first_only is True:
            return next(iter(definitions), None)
        else:
            return sorted(definitions, key=lambda d: (d.OwnerGroup, d.Name))
        
        
    def create_group(self, group_name):
        group_names = [g.Name for g in self.file.Groups]
        if group_name not in group_names:
            try:
                self.file.Groups.Create(group_name)
            except InvalidOperationException as err:
                print('Unable to create group: "{}". {}'.format(group_name, err))
                
    
    def create_definition(
        self,
        group_name, 
        name, 
        parameter_type, 
        description=None, 
        guid=None, 
        hide_no_value=False,
        visible=True
    ):
        group = self.find_group_by_name(group_name)
        if group:
            definitions = group.Definitions
            options = DB.ExternalDefinitionCreationOptions(name, parameter_type)
            if description:
                options.Description = description
            if guid:
                options.GUID = guid
            if visible is False:
                options.Visible = False
            if HOST_APP.is_newer_than(2020, or_equal=True):
                if hide_no_value is True:
                    options.HideWhenNoValue = True
            try:
                return definitions.Create(options)
            except ArgumentNullException as ne:
                print(ne)
            except ArgumentOutOfRangeException as re:
                print(re)
            except ArgumentException as ae:
                print('"{}" already exists: {}'.format(name, ae))
            

def extract_largest_index(string_list):
    largest_number = 0
    for string in string_list:
        match = re.search(r'\d+', string)
        if match:
            number = int(match.group())
            if number > largest_number:
                largest_number = number
    return largest_number
