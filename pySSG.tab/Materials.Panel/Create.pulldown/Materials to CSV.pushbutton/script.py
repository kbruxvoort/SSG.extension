# pylint: disable=import-error,invalid-name,broad-except
import csv

# import collections
import re


from pyrevit import revit, DB
from pyrevit import script
from pyrevit import forms

from collections import OrderedDict


class MatOption(forms.TemplateListItem):
    @property
    def name(self):
        """Mat Name"""
        try:
            # return '{}: {}'.format(revit.query.get_name(self.item), revit.doc.GetElement(self.item.AppearanceAssetId).Name)
            return "[{}] {}: {}".format(
                revit.doc.GetElement(self.item.AppearanceAssetId)
                .GetRenderingAsset()
                .Name,
                revit.query.get_name(self.item),
                revit.doc.GetElement(self.item.AppearanceAssetId).Name,
            )
        except AttributeError:
            return revit.query.get_name(self.item)


def toRGBColor(color):
    r = color.Red
    g = color.Green
    b = color.Blue

    return ",".join([str(r), str(g), str(b)])


def prop_by_name(schema_name, prop_name):
    patt = re.sub("Schema", "", schema_name)
    patt = re.sub("Prism", "Advanced", patt)

    nameSpace = DB.Visual
    schema = getattr(nameSpace, patt)
    prop = getattr(schema, prop_name)
    return prop


logger = script.get_logger()
forms.check_modeldoc(revit.doc, exitscript=True)

# make sure user is using 2019 or later
app = revit.doc.Application
if int(app.VersionNumber) < 2018:
    forms.alert("You must use Revit 2018 or newer to use this script.", exitscript=True)

selected_folder = forms.pick_folder()
if selected_folder:
    # layeredBottomF0 = Base Highlights Color, SurfaceNormal = Top Bump Map, LayeredNormal = Bottom Bump Map
    mat_schemas = {
        "PrismLayeredSchema": [
            "LayeredDiffuse",
            "LayeredBottomF0",
            "SurfaceNormal",
            "LayeredNormal",
        ],
        "PrismOpaqueSchema": ["OpaqueAlbedo", "SurfaceNormal"],
        "PrismMetalSchema": ["SurfaceAlbedo", "SurfaceNormal"],
        "GenericSchema": ["GenericDiffuse", "GenericBumpMap", "CommonTintColor"],
    }

    # col = sorted(DB.FilteredElementCollector(revit.doc).OfClass(DB.Material), key=lambda x: x.Name)
    col_mats = []
    col = DB.FilteredElementCollector(revit.doc).OfClass(DB.Material)
    for c in col:
        if revit.doc.GetElement(c.AppearanceAssetId):
            col_mats.append(c)

    col = sorted(
        col_mats,
        key=lambda x: revit.doc.GetElement(x.AppearanceAssetId)
        .GetRenderingAsset()
        .Name,
    )

    selected_mat = forms.SelectFromList.show(
        {
            "*All Materials": [MatOption(x) for x in col],
            # '*SSG Materials': [MatOption(x) for x in col if 'SSG' in x.Name]
            "Generic": [
                MatOption(x)
                for x in col
                if "GenericSchema"
                in revit.doc.GetElement(x.AppearanceAssetId).GetRenderingAsset().Name
            ],
            "Advanced Opaque": [
                MatOption(x)
                for x in col
                if "PrismOpaque"
                in revit.doc.GetElement(x.AppearanceAssetId).GetRenderingAsset().Name
            ],
            "Advanced Layered": [
                MatOption(x)
                for x in col
                if "PrismLayered"
                in revit.doc.GetElement(x.AppearanceAssetId).GetRenderingAsset().Name
            ],
            "Advanced Metal": [
                MatOption(x)
                for x in col
                if "PrismMetal"
                in revit.doc.GetElement(x.AppearanceAssetId).GetRenderingAsset().Name
            ],
            "Advanced Transparent": [
                MatOption(x)
                for x in col
                if "PrismTransparent"
                in revit.doc.GetElement(x.AppearanceAssetId).GetRenderingAsset().Name
            ],
        },
        multiselect=True,
        checked_only=True,
        button_name="Select Material",
    )

    if selected_mat:
        fieldnames = [
            "Name",
            "Base Schema",
            "Description",
            "Class",
            "Comments",
            "Manufacturer",
            "Model",
            "Cost",
            "URL",
            "Keynote",
            "Mark",
            "Use Render Appearance",
            "Shading Color",
            "Transparency",
            "Asset Name",
            "Asset Description",
            "Asset Keywords",
        ]

        assetProperties = []
        mat_list = []
        for mat in selected_mat:
            assetElem = revit.doc.GetElement(mat.AppearanceAssetId)
            renderingAsset = assetElem.GetRenderingAsset()
            # mat_dict = OrderedDict()
            mat_dict = {}

            # ----- IDENTITY TAB -----
            # Name
            mat_dict["Name"] = mat.Name

            # Description
            mat_dict["Description"] = mat.get_Parameter(
                DB.BuiltInParameter.ALL_MODEL_DESCRIPTION
            ).AsString()

            # Material Class
            mat_dict["Class"] = mat.MaterialClass

            # Comments
            mat_dict["Comments"] = mat.get_Parameter(
                DB.BuiltInParameter.ALL_MODEL_INSTANCE_COMMENTS
            ).AsString()

            # Keywords cannot be accessed through API

            # Manufacturer
            mat_dict["Manufacturer"] = mat.get_Parameter(
                DB.BuiltInParameter.ALL_MODEL_MANUFACTURER
            ).AsString()

            # Model
            mat_dict["Model"] = mat.get_Parameter(
                DB.BuiltInParameter.ALL_MODEL_MODEL
            ).AsString()

            # Cost
            mat_dict["Cost"] = mat.get_Parameter(
                DB.BuiltInParameter.ALL_MODEL_COST
            ).AsDouble()

            # URL
            mat_dict["URL"] = mat.get_Parameter(
                DB.BuiltInParameter.ALL_MODEL_URL
            ).AsString()

            # Keynote
            mat_dict["Keynote"] = mat.get_Parameter(
                DB.BuiltInParameter.KEYNOTE_PARAM
            ).AsString()

            # Mark
            mat_dict["Mark"] = mat.get_Parameter(
                DB.BuiltInParameter.ALL_MODEL_MARK
            ).AsString()

            # ----- GRAPHICS TAB -----
            # Use Render Appearance
            render_app = mat.UseRenderAppearanceForShading
            if render_app:
                use_render = 1
            else:
                use_render = 0
            mat_dict["Use Render Appearance"] = use_render

            # Shading Color
            mat_dict["Shading Color"] = toRGBColor(mat.Color)

            # Transparency
            mat_dict["Transparency"] = mat.Transparency

            # ----- APPEARANCE TAB -----
            with DB.Visual.AppearanceAssetEditScope(assetElem.Document) as editScope:
                editableAsset = editScope.Start(mat.AppearanceAssetId)

                # Asset Name
                mat_dict["Asset Name"] = editableAsset[
                    DB.Visual.SchemaCommon.UIName
                ].Value

                # Asset Description
                mat_dict["Asset Description"] = editableAsset[
                    DB.Visual.SchemaCommon.Description
                ].Value

                # Keywords
                mat_dict["Asset Keywords"] = editableAsset[
                    DB.Visual.SchemaCommon.Keyword
                ].Value

                # Schema
                mat_dict["Base Schema"] = editableAsset[
                    DB.Visual.SchemaCommon.BaseSchema
                ].Value

                try:
                    appProps = mat_schemas[mat_dict["Base Schema"]]
                    for schema_prop in appProps:
                        if schema_prop not in fieldnames:
                            fieldnames.append(schema_prop)

                        prop = editableAsset[
                            prop_by_name(mat_dict["Base Schema"], schema_prop)
                        ]
                        # print(prop.Type, type(prop.Type))

                        if prop.Type == DB.Visual.AssetPropertyType.Double4:
                            connectedAsset = prop.GetSingleConnectedAsset()
                            if not connectedAsset:
                                colorByte = prop.GetValueAsColor()
                                mat_dict[schema_prop] = ",".join(
                                    [
                                        str(colorByte.Red),
                                        str(colorByte.Blue),
                                        str(colorByte.Green),
                                    ]
                                )
                            else:
                                propBitmapProperty = connectedAsset[
                                    "unifiedbitmap_Bitmap"
                                ]
                                if propBitmapProperty:
                                    if "/" in propBitmapProperty.Value:
                                        # mat_dict[schema_prop] = propBitmapProperty.Value.split('/')[-1]
                                        mat_dict[schema_prop] = propBitmapProperty.Value
                                    else:
                                        # mat_dict[schema_prop] = propBitmapProperty.Value.split('\\')[-1]
                                        mat_dict[schema_prop] = propBitmapProperty.Value

                        elif prop.Type == DB.Visual.AssetPropertyType.Reference:
                            connectedAsset = prop.GetSingleConnectedAsset()
                            if connectedAsset:
                                propBitmapProperty = connectedAsset["bumpmap_Bitmap"]
                                if propBitmapProperty:
                                    if "/" in propBitmapProperty.Value:
                                        # mat_dict[schema_prop] = propBitmapProperty.Value.split('/')[-1]
                                        mat_dict[schema_prop] = propBitmapProperty.Value
                                    else:
                                        # mat_dict[schema_prop] = propBitmapProperty.Value.split('\\')[-1]
                                        mat_dict[schema_prop] = propBitmapProperty.Value
                        else:
                            mat_dict[schema_prop] = prop.Value
                except KeyError:
                    print("This material does not used a preapproved schema")

            mat_list.append(mat_dict)
            # editScope.Commit(True)
            # editScope.Cancel()

        try:
            with open(selected_folder + "\\revit_mats.csv", "w") as new_file:
                # fieldnames = set(fieldnames)
                csv_writer = csv.DictWriter(
                    new_file, fieldnames=fieldnames, lineterminator="\n"
                )

                csv_writer.writeheader()
                for m in mat_list:
                    # print(m)
                    csv_writer.writerow(m)
                # forms.alert('Materials have been successfully exported to "{}"'.format(selected_folder+'\\revit_mats.csv'))
                forms.toast(
                    "The materials have been successfully exported to csv",
                    title="Material CSV",
                    appid="Materials to CSV",
                    click=selected_folder + "\\revit_mats.csv",
                    actions={"Open File": selected_folder + "\\revit_mats.csv"},
                )
        except IOError:
            message = '"revit_mats.csv" is currently open and must be closed before this script can run.'
            logger.error(message)