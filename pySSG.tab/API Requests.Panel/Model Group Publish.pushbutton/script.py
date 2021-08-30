import json
import math

from System.Net import WebClient

from pyrevit import revit, DB
from fetchbim import settings
from fetchbim.family import Family, GroupedFamily
from fetchbim.attributes import Parameter


def is_close(number):
    if -0.001 <= number <= 0.001:
        number = 0
    return number


if settings.BIM_KEY:
    builtInCat = DB.BuiltInCategory.OST_IOSModelGroups

    group = revit.selection.pick_element_by_category(
        builtInCat, message="PICK A STUPID GROUP IDIOT"
    )
    if group:
        group_type = group.GroupType
        group_type_params = group_type.Parameters
        category_name = "Model Group/Test"
        group_name = "Enter Group Name"
        category_param = [
            x for x in group_type_params if x.Definition.Name == "CategoryName"
        ]
        group_name_param = [
            x for x in group_type_params if x.Definition.Name == "Group Name"
        ]
        if category_param:
            category_name = category_param[0].AsString()
        if group_name_param:
            group_name = group_name_param[0].AsString()
        group_members = group.GetMemberIds()
        members = [revit.doc.GetElement(id) for id in group_members]

        min_list = []
        max_list = []
        for family in members:
            bbox = family.get_BoundingBox(None)
            min_list.append((bbox.Min.X, bbox.Min.Y, bbox.Min.Z))
            max_list.append((bbox.Max.X, bbox.Max.Y, bbox.Max.Z))

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
        bbox_family = GroupedFamily(
            settings.BOUNDING_BOX_ID,
            settings.BOUNDING_BOX_TYPE_ID,
            Parameters=[
                Parameter("Width", Width, DataType="Length"),
                Parameter("Depth", Depth, DataType="Length"),
                Parameter("Height", Height, DataType="Length"),
                Parameter("Group Name", group_name, DataType="Text"),
                Parameter("ENTER_Shape Number", 1, DataType="Integer"),
            ],
        )
        bbox_family.ProjectId = None
        GroupedFamilies.append(bbox_family)
        ChildFamilies = []
        print(group.Name)
        print("Width={}, Depth={}, Height={}".format(Width, Depth, Height))
        print("Instances: ")
        for family in members:
            parent_family = family.SuperComponent
            if not parent_family:
                host = family.Host

                rot = math.degrees(family.Location.Rotation)
                print("\t{}: {}".format(family.Symbol.FamilyName, family.Name))
                print(
                    "\t\tX={}, Y={}, Rotation={}".format(
                        family.Location.Point.X - minX,
                        family.Location.Point.Y - maxY,
                        rot,
                    )
                )
                type_params = family.Symbol.Parameters
                ssgfid = [
                    x.AsString() for x in type_params if x.Definition.Name == "SSGFID"
                ]
                ssgtid = [
                    x.AsString() for x in type_params if x.Definition.Name == "SSGTID"
                ]
                if ssgfid:
                    print("\t\tSSGFID: {}".format(ssgfid[0]))
                else:
                    raise AttributeError(
                        "{} is missing SSGFID parameter".format(
                            family.Symbol.FamilyName
                        )
                    )
                if ssgtid:
                    print("\t\tSSTFID: {}".format(ssgtid[0]))
                else:
                    raise AttributeError(
                        "{} is missing SSGTID parameter".format(
                            family.Symbol.FamilyName
                        )
                    )
                if host:
                    print("\t\tHosted to {}".format(host.Symbol.FamilyName))
                    child_fam = GroupedFamily(
                        ssgfid[0],
                        ssgtid[0],
                        Width=is_close(round(family.Location.Point.X - minX, 7)),
                        Depth=is_close(round(family.Location.Point.Y - maxY, 7)),
                        Rotation=rot,
                    )
                    child_fam.HostProjectId = host.Id.IntegerValue
                    child_fam.ProjectId = family.Id.IntegerValue
                    double_nested = False
                    for child in ChildFamilies:
                        if child.ProjectId == child_fam.HostProjectId:
                            child.ChildModelGroups.append(child_fam)
                            double_nested = True
                    if double_nested is False:
                        ChildFamilies.append(child_fam)
                else:
                    fam = GroupedFamily(
                        ssgfid[0],
                        ssgtid[0],
                        Width=is_close(round(family.Location.Point.X - minX, 7)),
                        Depth=is_close(round(family.Location.Point.Y - maxY, 7)),
                        Rotation=rot,
                    )
                    fam.ProjectId = family.Id.IntegerValue
                    GroupedFamilies.append(fam)

        for child in ChildFamilies:
            for grouped_fam in GroupedFamilies:
                if child.HostProjectId == grouped_fam.ProjectId:
                    grouped_fam.ChildModelGroups.append(child)

        model_group = Family(
            group.Name,
            LoadMethod=1,
            CategoryName=category_name,
            FamilyObjectType="ModelGroup",
            GroupedFamilies=GroupedFamilies,
        )

        data = model_group.to_json()

        print("Publishing Group")
        url = settings.POST_FAMILY
        client = WebClient()
        client.Headers.Add("Authorization", "Bearer " + settings.BIM_KEY)
        client.Headers.Add("Accept", "application/json")
        client.Headers.Add("Content-Type", "application/json")
        response = client.UploadString(url, "POST", data)
        response_dict = json.loads(response)
        print("\tSSGFID: {}".format(response_dict["Id"]))
else:
    print("Authorization key needed to run this script")
