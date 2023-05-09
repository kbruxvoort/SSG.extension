from pyrevit import revit, DB, forms


class RoomOption(forms.TemplateListItem):
    @property
    def name(self):
        """Room name."""
        return "%s" % revit.query.get_name(self.item)


def get_placed_rooms(project_document, active_view_only=False):
    area_param_id = DB.ElementId(DB.BuiltInParameter.ROOM_AREA)
    area_param_prov = DB.ParameterValueProvider(area_param_id)
    param_greater = DB.FilterNumericGreater()
    parameter_filter = DB.ElementParameterFilter(
        DB.FilterDoubleRule(area_param_prov, param_greater, 0, 1e-6)
    )
    if active_view_only is True:
        return DB.FilteredElementCollector(project_document, project_document.ActiveView.Id) \
                                          .WherePasses(parameter_filter).ToElements()
    else:
        return DB.FilteredElementCollector(project_document) \
                                          .WherePasses(parameter_filter).ToElements()


def select_placed_rooms(project_document, active_view_only=False):
    rooms = get_placed_rooms(project_document, active_view_only)
    selected = forms.SelectFromList.show(
            sorted([RoomOption(x) for x in rooms], key=lambda x: x.Number),
            multiselect=True,
            button_name="Select Rooms",
        )
    return selected


def get_name(room):
    name_param = room.get_Parameter(DB.BuiltInParameter.ROOM_NAME)
    if name_param:
        return name_param.AsString()
                

def get_number(room):
    number_param = room.get_Parameter(DB.BuiltInParameter.ROOM_NUMBER)
    if number_param:
        return number_param.AsString()
    
def create_expanded_bounding_box(room, view=None, x=(1,1), y=(1,1), z=(0,0)):
    room_bounding_box = room.get_BoundingBox(view)
    box_max = room_bounding_box.Max
    box_min = room_bounding_box.Min
    new_box_max = DB.XYZ(box_max.X + x[0], box_max.Y + y[0], box_max.Z + z[0])
    new_box_min = DB.XYZ(box_min.X - x[1], box_min.Y - y[1], box_min.Z - z[1])
    new_bounding_box = DB.BoundingBoxXYZ()
    new_bounding_box.Max = new_box_max
    new_bounding_box.Min = new_box_min
    return new_bounding_box

def get_center(room):
    closed_shell = room.ClosedShell
    for elem in closed_shell:
        if isinstance(elem, DB.Solid):
            return elem.ComputeCentroid()
