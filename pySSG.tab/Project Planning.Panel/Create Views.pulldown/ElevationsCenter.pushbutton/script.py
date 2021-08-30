# pylint: disable=import-error,invalid-name,broad-except
from pyrevit import revit, DB
from pyrevit import script
from pyrevit import forms

from Autodesk.Revit import Exceptions


class RoomOption(forms.TemplateListItem):
    # def __init__(self, room_element):
    #     super(RoomOption, self).__init__(room_element)

    @property
    def name(self):
        """Room name."""
        return "%s" % revit.query.get_name(self.item)


output = script.get_output()
logger = script.get_logger()

categories = [DB.BuiltInCategory.OST_Rooms]
rooms = [x for x in revit.query.get_elements_by_categories(categories) if x.Area > 0]

if rooms:

    type_name = "Interior Elevation"
    view_types = [
        x
        for x in revit.query.get_types_by_class(DB.ViewFamilyType)
        if revit.query.get_name(x) == type_name
    ]

    if view_types:

        res = forms.SelectFromList.show(
            sorted([RoomOption(x) for x in rooms], key=lambda x: x.Number),
            multiselect=True,
            # name_attr= 'Number',
            button_name="Select Rooms",
        )

        if res:
            total_work = len(res)

            with revit.Transaction("Create Elevations"):
                for idx, r in enumerate(res):
                    roomName = r.get_Parameter(DB.BuiltInParameter.ROOM_NAME).AsString()
                    roomNumber = r.get_Parameter(
                        DB.BuiltInParameter.ROOM_NUMBER
                    ).AsString()
                    bbox = r.get_BoundingBox(revit.doc.ActiveView)
                    rMin = bbox.Min
                    rMax = bbox.Max
                    roomCenter = (rMin + rMax) / 2.0

                    eleMarker = DB.ElevationMarker.CreateElevationMarker(
                        revit.doc, view_types[0].Id, roomCenter, 100
                    )
                    ele1 = eleMarker.CreateElevation(
                        revit.doc, revit.doc.ActiveView.Id, 1
                    )
                    ele2 = eleMarker.CreateElevation(
                        revit.doc, revit.doc.ActiveView.Id, 2
                    )
                    ele3 = eleMarker.CreateElevation(
                        revit.doc, revit.doc.ActiveView.Id, 3
                    )
                    ele4 = eleMarker.CreateElevation(
                        revit.doc, revit.doc.ActiveView.Id, 0
                    )
                    newName = "Elevation - " + roomName + " " + roomNumber + " - "
                    # print(newName)

                    try:
                        print(
                            'Creating Elevations for  "%s - %s"'
                            % (roomNumber, roomName)
                        )
                        revit.update.set_name(ele1, newName + "North")
                        revit.update.set_name(ele2, newName + "East")
                        revit.update.set_name(ele3, newName + "South")
                        revit.update.set_name(ele4, newName + "West")

                    except Exceptions.ArgumentException:
                        message = "View Name already exists."
                        logger.warning(message)

                    output.update_progress(idx + 1, total_work)

            print("Completed\n")
        else:
            print("No Rooms Selected")
    else:
        print("No View Type Match for " + type_name)
else:
    print("No Rooms Found")
