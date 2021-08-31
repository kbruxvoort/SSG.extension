import json

from math import ceil, degrees

from System.Net import WebClient

from pyrevit import revit, DB
from fetchbim import settings
from fetchbim.family import Family, GroupedFamily
from fetchbim.attributes import Parameter


def isclose(a, b, rel_tol=1e-9, abs_tol=0.0):
    return abs(a - b) <= max(rel_tol * max(abs(a), abs(b)), abs_tol)


def normalize_number(number):
    if isclose(number, number // 1, abs_tol=0.001):
        return number // 1
    elif isclose(number, ceil(number), abs_tol=0.001):
        return ceil(number)
    else:
        return round(number, 4)


def normalize_angle(angle):
    return int(round(angle, 0) % 360)


BUILTIN_KEEP = ["Width", "Depth", "Height"]
# ROUND_DIGITS = 3


if settings.BIM_KEY:
    builtInCat = DB.BuiltInCategory.OST_IOSModelGroups

    group = revit.selection.pick_element_by_category(
        builtInCat, message="select a model group"
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

        Width = normalize_number(maxX - minX)
        Depth = normalize_number(maxY - minY)
        Height = normalize_number(maxZ - minZ)

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
            Parameters = []
            parent_family = family.SuperComponent
            if not parent_family:
                host = family.Host
                rot = normalize_angle(degrees(family.Location.Rotation))
                print("\t{}: {}".format(family.Symbol.FamilyName, family.Name))
                print(
                    "\t\tX={}, Y={}, Rotation={}".format(
                        normalize_number(family.Location.Point.X - minX),
                        normalize_number(family.Location.Point.Y - maxY),
                        rot,
                    )
                )
                instance_params = family.Parameters
                for param in instance_params:
                    if param.IsReadOnly is False:
                        if (
                            param.Definition.BuiltInParameter
                            == DB.BuiltInParameter.INVALID
                            or param.Definition.Name in BUILTIN_KEEP
                        ):
                            if param.Definition.Name.startswith("z") == False:
                                # print(param.Definition.Name, param.Definition.ParameterType)
                                if (
                                    param.Definition.ParameterType
                                    == DB.ParameterType.Length
                                ):
                                    p = Parameter(
                                        param.Definition.Name,
                                        normalize_number(param.AsDouble()),
                                        DataType="Length",
                                    )
                                    Parameters.append(p)
                                elif (
                                    param.Definition.ParameterType
                                    == DB.ParameterType.Integer
                                ):
                                    p = Parameter(
                                        param.Definition.Name,
                                        param.AsInteger(),
                                        DataType="Integer",
                                    )
                                    Parameters.append(p)
                                elif (
                                    param.Definition.ParameterType
                                    == DB.ParameterType.YesNo
                                ):
                                    p = Parameter(
                                        param.Definition.Name,
                                        param.AsInteger(),
                                        DataType="Boolean",
                                    )
                                    Parameters.append(p)

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
                        Width=normalize_number(
                            normalize_number(family.Location.Point.X - minX)
                        ),
                        Depth=normalize_number(
                            normalize_number(family.Location.Point.Y - maxY)
                        ),
                        Rotation=rot,
                        Parameters=Parameters,
                    )
                    # print(repr(Parameters))
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
                        Width=normalize_number(
                            normalize_number(family.Location.Point.X - minX)
                        ),
                        Depth=normalize_number(
                            normalize_number(family.Location.Point.Y - maxY)
                        ),
                        Rotation=rot,
                        Parameters=Parameters,
                    )
                    # print(repr(Parameters))
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
