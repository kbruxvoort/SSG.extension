import sys
sys.path.append(r'Z:\Kyle\Python Projects\fetchbim')

import os
import json
import math
from System.Net import WebClient
# import requests
from pyrevit import revit, DB
from pyrevit.revit import selection
from fetchbim.family import Family, GroupedFamily
from fetchbim import settings

DEV_KEY = os.environ.get('DEV_KEY')


def is_close(number):
    if -.001 <= number <= .001:
        number = 0
    return number


builtInCat = DB.BuiltInCategory.OST_IOSModelGroups

group = selection.pick_element_by_category(builtInCat, message='PICK A STUPID GROUP IDIOT')
if group:
    group_members = group.GetMemberIds()
    members = [revit.doc.GetElement(id) for id in group_members]

    min_list = []
    max_list = []
    for family in members:
        bbox = family.get_BoundingBox(None)
        # fam_width = bbox.Max.X - bbox.Min.X
        # fam_depth = bbox.Max.Y - bbox.Min.Y
        # fam_height = bbox.Max.Z - bbox.Min.Z
        min_list.append((bbox.Min.X, bbox.Min.Y, bbox.Min.Z))
        max_list.append((bbox.Max.X, bbox.Max.Y, bbox.Max.Z)) 
        # print(fam_width, fam_depth, fam_height)

    minX = min([x[0] for x in min_list])
    minY = min([x[1] for x in min_list])
    minZ = min([x[2] for x in min_list])
    maxX = max([x[0] for x in max_list])
    maxY = max([x[1] for x in max_list])
    maxZ = max([x[2] for x in max_list])

    Width = maxX - minX
    Depth = maxY - minY
    Height = maxZ - minZ

    GroupedFamilies = []
    ChildFamilies = []
    print(group.Name)
    print("Width={}, Depth={}, Height={}".format(Width, Depth, Height))
    print('Instances: ')
    for family in members:
        parent_family = family.SuperComponent
        if not parent_family:
            host = family.Host
            
            rot = math.degrees(family.Location.Rotation)
            print("\t{}: {}".format(family.Symbol.FamilyName, family.Name))
            print("\t\tX={}, Y={}, Rotation={}".format(family.Location.Point.X - minX, family.Location.Point.Y - maxY, rot))
            type_params = family.Symbol.Parameters
            ssgfid = [x.AsString() for x in type_params if x.Definition.Name == 'SSGFID']
            ssgtid = [x.AsString() for x in type_params if x.Definition.Name == 'SSGTID']
            if ssgfid:
                print('\t\tSSGFID: {}'.format(ssgfid[0]))
            if ssgtid:
                print('\t\tSSTFID: {}'.format(ssgtid[0]))
            if host:
                # print("\t\t{}".format(host))
                print("\t\tHosted to {}".format(host.Symbol.FamilyName))
                child_fam = GroupedFamily(ssgfid[0], ssgtid[0], Width=is_close(round(family.Location.Point.X - minX, 7)), Depth=is_close(round(family.Location.Point.Y - maxY, 7)), Rotation=rot)
                child_fam.HostProjectId = host.Id.IntegerValue
                ChildFamilies.append(child_fam)
            else:
                fam = GroupedFamily(ssgfid[0], ssgtid[0], Width=is_close(round(family.Location.Point.X - minX, 7)), Depth=is_close(round(family.Location.Point.Y - maxY, 7)), Rotation=rot)
                fam.ProjectId = family.Id.IntegerValue
                GroupedFamilies.append(fam)
    for child in ChildFamilies:
        for grouped_fam in GroupedFamilies:
            if child.HostProjectId == grouped_fam.ProjectId:
                grouped_fam.ChildModelGroups.append(child)

    model_group = Family(group.Name, LoadMethod=1, CategoryName='Model Group/Test', FamilyObjectType='ModelGroup', GroupedFamilies=GroupedFamilies)

    print(repr(model_group))


    data = model_group.to_json()
    print(data)

    print('Publishing Group')
    url = 'https://fetch.devssg.com/api/v2/Family/'
    client = WebClient()
    client.Headers.Add("Authorization", 'Bearer ' + DEV_KEY)
    client.Headers.Add("Accept", "application/json")
    client.Headers.Add("Content-Type", "application/json")
    print(client.UploadString(url, "POST", data))