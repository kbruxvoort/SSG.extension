from pyrevit import revit, DB


room_tags = DB.FilteredElementCollector(revit.doc, revit.active_view.Id) \
              .OfCategory(DB.BuiltInCategory.OST_RoomTags) \
              .WhereElementIsNotElementType() \
              .ToElements()

area_param_id = DB.ElementId(DB.BuiltInParameter.ROOM_AREA)
area_param_prov = DB.ParameterValueProvider(area_param_id)
param_greater = DB.FilterNumericGreater()
area_value_rule = DB.FilterDoubleRule(
    area_param_prov,
    param_greater,
    0,
    1E-6
)
param_filter = DB.ElementParameterFilter(area_value_rule)

rooms = DB.FilteredElementCollector(revit.doc, revit.active_view.Id) \
          .WherePasses(param_filter) \
          .ToElements()

if rooms:
    with revit.Transaction("Center Rooms"):
        for room in rooms:
            closed_shell = room.ClosedShell
            for elem in closed_shell:
                if isinstance(elem, DB.Solid):
                    center = elem.ComputeCentroid()
                    room.Location.Move(center - room.Location.Point)
                    for tag in room_tags:
                        if tag.Room.Id == room.Id:
                            tag.Location.Move(center - tag.Location.Point)
                            break
                    break
