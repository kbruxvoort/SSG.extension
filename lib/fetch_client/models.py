import base64


class BaseModel(object):
    def to_dict(self, include=None, exclude=None):
        result = {}
        for key, value in self.__dict__.items():
            if include and key not in include:
                continue
            if exclude and key in exclude:
                continue
            if isinstance(value, BaseModel):
                result[key] = value.to_dict(include, exclude)
            elif isinstance(value, list):
                result[key] = []
                for item in value:
                    if isinstance(item, BaseModel):
                        result[key].append(item.to_dict(include, exclude))
                    else:
                        result[key].append(item)
            else:
                result[key] = value
        return result
    
        # attrs = self.__dict__.copy()
        # if include:
        #     attrs = {k: v for k, v in attrs.items() if k in include}
        # elif exclude:
        #     attrs = {k: v for k, v in attrs.items() if k not in exclude}
        # for k, v in attrs.items():
        #     if isinstance(v, BaseModel):
        #         attrs[k] = v.to_dict()
        #     elif isinstance(v, list):
        #         attrs[k] = [item.to_dict() if isinstance(item, BaseModel) else item for item in v]
        # return attrs
    
    def __str__(self):
        attributes = vars(self)
        return "{}: {}".format(attributes.get('Id'), attributes.get('Name'))
    
    def __repr__(self):
        class_name = type(self).__name__
        attributes = vars(self)
        attribute_strings = []
        for attribute in attributes:
            value = attributes[attribute]
            attribute_strings.append("{}={}".format(attribute, value))
        attribute_string = ", ".join(attribute_strings)
        return "{}({})".format(class_name, attribute_string)
    
    @classmethod
    def from_dict(cls, data):
        return cls(**data)
    
    
class Property(BaseModel):
    def __init__(self, Name, Value, Id=None, Deleted=False, **kwargs):
        self.Name = Name
        self.Value = Value
        self.Id = Id
        self.Deleted = Deleted
        
        
class Parameter(BaseModel):
    def __init__(self, Name, Value, ParameterId=None, ParameterType="Type", DataType="Text", Sort=0, Hidden=False, Deleted=False, **kwargs):
        self.Name = Name
        self.Value = Value
        self.ParameterId = ParameterId
        self.ParameterType = ParameterType
        self.DataType = DataType
        self.Sort = Sort
        self.Hidden = Hidden
        self.Deleted = Deleted

    
        
class File(BaseModel):
    def __init__(self, FileName, FileExtension, FileId=None, FileKey="FamilyRevitFile", FileData=None, Deleted=False, **kwargs):
        self.FileName = FileName
        self.FileExtension = FileExtension
        self.FileId = FileId
        self.FileKey = FileKey
        self.FileData = FileData
        self.Deleted = Deleted
        
    # def to_dict(self):
    #     exclude = ['Path']
    #     return super().to_dict(exclude=exclude)
    
    
    @classmethod
    def file_from_path(cls, file_path, file_key):
        try:
            with open(file_path, "rb") as file:
                byteform = base64.b64encode(file.read())
                file_data = byteform.decode("utf-8")
                file_name, extension = file_path.split("\\")[-1].split(".")
                return cls(FileName=file_name, FileExtension="." + extension, FileKey=file_key, FileData=file_data)
        except TypeError as e:
            print("File path is incorrect: {}".format(e))
            
        
class Category(BaseModel):
    def __init__(self, CategoryName, CategoryType="Markets", **kwargs):
        self.CategoryName = CategoryName
        self.CategoryType = CategoryType
        
    
              
class FamilyType(BaseModel):
    def __init__(self, Name, Id=None, IsDefault=False, Deleted=False, Files=None, Parameters=None, **kwargs):
        self.Id = Id
        self.Name = Name
        self.IsDefault = IsDefault
        self.Deleted = Deleted
        self.Files = Files or []
        self.Parameters = Parameters or []
        
    
    @classmethod    
    def from_dict(cls, data):
        param_list = data.pop('Parameters', [])
        file_list = data.pop('Files', [])
        obj = cls(**data)
        if param_list:
            obj.Parameters = [Parameter.from_dict(p) for p in param_list]
        if file_list:
            obj.Files = [File.from_dict(f) for f in file_list]
        return obj
    
    
class GroupedFamily(BaseModel):
    def __init__(self, ModelGroupId=None, ChildFamilyId=None, FamilyTypeId=None, InstanceCount=1, 
                 Sort=0, Width=0, Depth=0, Rotation=0, Deleted=False, Parameters=None, 
                 ChildFamilyName=None, ChildModelGroups=None, **kwargs):
        self.ModelGroupId = ModelGroupId
        self.ChildFamilyId = ChildFamilyId
        self.FamilyTypeId = FamilyTypeId
        self.InstanceCount = InstanceCount
        self.Sort = Sort
        self.Width = Width
        self.Depth = Depth
        self.Rotation = Rotation
        self.Deleted = Deleted
        self.Parameters = Parameters or []
        self.ChildFamilyName = ChildFamilyName
        self.ChildModelGroups = ChildModelGroups or []    

        
    @classmethod
    def from_dict(cls, data):
        param_list = data.pop('Parameters', [])
        child_list = data.pop('ChildModelGroups', [])
        obj = cls(**data)
        if param_list:
            obj.Parameters = [Parameter.from_dict(p) for p in param_list]
        if child_list:
            obj.ChildModelGroups = [GroupedFamily.from_dict(c) for c in child_list]
        return obj
    
    
class Family(BaseModel):
    def __init__(self, Name, Id=None, CategoryName=None, FamilyObjectType="Family", LoadMethod=0, 
                 Status=2, GroupedFamilies=None, FamilyTypes=None, AdditionalCategories=None, 
                 Deleted=False, Files=None, Parameters=None, **kwargs):
        self.Id = Id
        self.Name = Name
        self.CategoryName = CategoryName
        self.FamilyObjectType = FamilyObjectType
        self.LoadMethod = LoadMethod
        self.Status = Status
        self.GroupedFamilies = GroupedFamilies or []
        self.FamilyTypes = FamilyTypes or []
        self.AdditionalCategories = AdditionalCategories or []
        self.Deleted = Deleted
        self.Files = Files or []
        self.Parameters = Parameters or []
        
    
    @classmethod    
    def from_dict(cls, data):
        param_list = data.pop('Parameters', [])
        file_list = data.pop('Files', [])
        group_list = data.pop('GroupedFamilies', [])
        fam_type_list = data.pop('FamilyTypes', [])
        cat_list = data.pop('AdditionalCategories', [])
        obj = cls(**data)
        if param_list:
            obj.Parameters = [Parameter.from_dict(p) for p in param_list]
        if file_list:
            obj.Files = [File.from_dict(f) for f in file_list]
        if group_list:
            obj.GroupedFamilies = [GroupedFamily.from_dict(g) for g in group_list]
        if fam_type_list:
            obj.FamilyTypes = [FamilyType.from_dict(t) for t in fam_type_list]
        if cat_list:
            obj.AdditionalCategories = [Category.from_dict(c) for c in cat_list]
        return obj