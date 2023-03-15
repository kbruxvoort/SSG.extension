from pyrevit import revit, DB
from Autodesk.Revit.Exceptions import ArgumentException


def set_room_bounding(link, boolean_int):
    link_type = revit.doc.GetElement(link.GetTypeId())
    bounding_param = link_type.get_Parameter(DB.BuiltInParameter.WALL_ATTR_ROOM_BOUNDING)
    if boolean_int == 1 or 0:
        with revit.Transaction("Set Link to Room Bounding"):
            bounding_param.Set(boolean_int)
    
    

def get_linked_levels(link_doc):
    # link_doc = link.GetLinkDocument()
    link_levels = (
        DB.FilteredElementCollector(link_doc)
        .OfCategory(DB.BuiltInCategory.OST_Levels)
        .WhereElementIsNotElementType()
        .ToElements()
    )
    return link_levels

        
def copy_linked_levels(link):
    current_levels = (
        DB.FilteredElementCollector(revit.doc)
        .OfCategory(DB.BuiltInCategory.OST_Levels)
        .WhereElementIsNotElementType()
        .ToElements()
    )
    linked_levels = get_linked_levels(link)
    with revit.Transaction("Copy linked levels"):
        existing_levels, copied_levels = [], []
        
        for level in sorted(linked_levels, key=lambda x: x.Elevation):
            match = False
            # print(level.Name, level.Elevation)
            # level_name = level.LookupParameter("Name").AsString()
            
            for c in current_levels:
                # print(c.Name, c.Elevation)
                # print(abs(level.Elevation - c.Elevation))
                if abs(level.Elevation - c.Elevation) < .1:
                    # level.Name = c.Name
                    existing_levels.append((c, level.Name, level.Elevation))
                    match = True
                    break
                    
            
            # if level.Elevation in [c.Elevation for c in current_levels]:
            #     print(level_name + " match")
            #     copied_levels.append(level)
            if match == False:
                new_level = DB.Level.Create(revit.doc, level.Elevation)
                # name_param = level.get_Parameter(DB.BuiltInParameter.LEVEL_NAME)
                try:
                    new_level.Name = level.Name
                except ArgumentException as ae:
                    print("{}: {}".format(level.Name, ae))
                    
                copied_levels.append(new_level)
    # print(existing_levels)
    # print(copied_levels)
    return existing_levels, copied_levels
                
def update_levels_from_link(existing_levels):
    with revit.Transaction("Update levels"):
        for level, name, elevation in existing_levels:
            level.Elevation = elevation
            level.Name = name
            # name_param = level.get_Parameter(DB.BuiltInParameter.LEVEL_NAME)
            # name_param.Set(name)
            # elev_param = level.get_Parameter(DB.BuiltInParameter.LEVEL_ELEV)
            # elev_param.Set(elevation)

def create_plans_from_levels(levels):
    plans = []
    with revit.Transaction("Create plans from levels"):
        for level in levels:
            plan_type_id = revit.doc.GetDefaultElementTypeId(DB.ElementTypeGroup.ViewTypeFloorPlan)
            plan = DB.ViewPlan.Create(revit.doc, plan_type_id, level.Id)
            plans.append(plan)
    return plans
    

def get_linked_rooms_by_level(link_doc, doc):
    # link_doc = link.GetLinkDocument()
    # current_levels = (
    #     DB.FilteredElementCollector(revit.doc)
    #     .OfCategory(DB.BuiltInCategory.OST_Levels)
    #     .WhereElementIsNotElementType()
    #     .ToElements()
    # )
    # link_views = (
    #     DB.FilteredElementCollector(link_doc)
    #     .OfCategory(DB.BuiltInCategory.OST_Views)
    #     .OfClass(DB.ViewPlan)
    #     .ToElements()
    # )
    # view_level = None
    # for v in link_views:
    #     if v.GenLevel:
    #         for c in current_levels:
    #             if v.GenLevel.Elevation == c.Elevation:
    #                 view_level = c
                    # break
            # if v.GenLevel.Elevation == doc.ActiveView.GenLevel.Elevation:
            #     view_level = v
            #     break
            
    linked_rooms = (
        DB.FilteredElementCollector(link_doc)
        .OfCategory(DB.BuiltInCategory.OST_Rooms)
        .ToElements()
    )

    rooms = []
    for r in linked_rooms:
        if r.Area > 0:
            rooms.append(r)
    return rooms
    
def rooms_boundaries(room):
    level = room.Level
    number = room.Number
    name = room.LookupParameter("Name").AsString()
    opt = DB.SpatialElementBoundaryOptions()
    boundaries = room.GetBoundarySegments(opt)
    curves = []
    for segment in boundaries:
        for b in segment:
            curve = b.GetCurve()
            curves.append(curve)
    position = room.Location
    return name, number, level, curves, position.Point

def recreate_room(linked_room):
    # curveArr =  DB.CurveArray()
    # for c in linked_room[3]: 
    #     curveArr.Append(c )

    # revit.doc.Create.NewRoomBoundaryLines( revit.doc.ActiveView.SketchPlane,curveArr, revit.doc.ActiveView )    

    
    with revit.Transaction("Recreate linked rooms"):
        tagPoint =  DB.UV( linked_room[4].X,  linked_room[4].Y )
        room = revit.doc.Create.NewRoom( revit.doc.ActiveView.GenLevel, tagPoint )
        room.Number = linked_room[1]
        room.Name = linked_room[0]
    
    # tag room
    # roomTag = revit.doc.Create.NewRoomTag(room.Id, tagPoint, revit.doc.ActiveView.Id)
    # roomTag.RoomTagType = room_tag.RoomTagType
    # default_tag = revit.doc.GetDefaultElementTypeId(DB.ElementTypeGroup.ViewTypeElevation)
    
    return room

if __name__ == '__main__':
    link = revit.selection.pick_element(message='Select Revit Link')
    if link:
        set_room_bounding(link, 1)
        levels = copy_linked_levels(link.GetLinkDocument())
        update_levels_from_link(levels[0])
        plans = create_plans_from_levels(levels[1])
        # # for r in sorted(rooms, key=lambda x: x.Number):
        # #     print("{} - {}".format(r.Number, r.LookupParameter('Name').AsString()))
        # with revit.Transaction("Recreate linked rooms"):
        for r in get_linked_rooms_by_level(link.GetLinkDocument(), revit.doc):
        #         print(r.Number, r.Location.Point.X, r.Location.Point.Y, r.Area)
            room = rooms_boundaries(r)
            new_room = recreate_room(room)
        #             # revit.doc.Create.NewRoomTag(new_room.Id, DB.UV(0,0), None)
                    
        #         except Exception as e:
        #             print(e)
                





