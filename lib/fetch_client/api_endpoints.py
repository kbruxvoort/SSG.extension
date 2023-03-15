import requests

class Endpoint(object):
    def __init__(self, parent):
        self.parent = parent
        # self.endpoint = endpoint

    # def request(self, path=None, method='GET', params=None, data=None, headers=None, **kwargs):
    #     return self.client.request(
    #         path=path,
    #         method=method,
    #         params=params,
    #         data=data,
    #         headers=headers
    #     )

class FamiliesEndpoint(Endpoint):
    def __init__(self, parent):
        super(FamiliesEndpoint, self).__init__(parent=parent)

    def list(self):
        # return self.request(path="Families/All", method='GET')
        response = requests.get("https://bimservice.ssgbim.com/api/Families/All")
        if response.ok:
            return response.json()

    def retrieve(self, family_id):
        response = self.parent.request(path="v2/Home/Family/{}".format(family_id), method='GET')
        if response.get('BusinessFamilies'):
            return response.get('BusinessFamilies')[-1]
        
    def create(self, data):
        return self.parent.request(path="v2/Family", method="POST", data=data)
    
    def update(self, data):
        return self.parent.request(path="/Family", method="PATCH", data=data)
    
    def search(
        self,
        family_id=None,
        family_object_type=None,
        category_name=None,
        parameter_name=None,
        parameter_value=None,
        parameter_match_type=None,
        property_name=None,
        property_value=None,
        property_match_type=None,
        file_key=None
        ):
        
        data = {}
        data["FamilyId"] = family_id
        data["FamilyObjectType"] = family_object_type
        data["CategoryName"] = category_name
        data["ParameterName"] = parameter_name
        data["ParameterValue"] = parameter_value
        data["ParameterValueMatchType"] = parameter_match_type
        data["PropertyName"] = property_name
        data["PropertyValue"] = property_value
        data["PropertyValueMatchType"] = property_match_type
        data["FileKey"] = file_key
        
        return self.parent.request(path="/SharedFile/Families", method="POST", data=data)


class FilesEndpoint(Endpoint):
    def __init__(self, parent):
        super(FilesEndpoint, self).__init__(parent=parent)

    def list(self):
        return self.parent.request(path="Files", method='GET')
    
    def create(self, file_name, extension, file_data, file_key):
        data = {
            "FileName": file_name,
            "FileExtension": extension,
            "FileData": file_data,
            "FileKey": file_key
        }
        return self.parent.request(path="Files", method="POST", data=data)
    
    def attach_to_families(self, family_ids, file_id):
        data = [{"FamilyId": family_id, "FileId": file_id} for family_id in family_ids]
        return self.parent.request(path="FamilyFiles", method="POST", data=data)
    

class SharedRulesEndpoint(Endpoint):
    def __init__(self, parent):
        super(SharedRulesEndpoint, self).__init__(parent=parent)

    def list(self):
        response = self.parent.request(path="SharedFiles", method='GET')
        if response.get('SharedFiles'):
            return response.get('SharedFiles')
