"""This script batch creates materials from an excel template. You must use Revit 2019 or newer to have access to appearance assets"""


#pylint: disable=import-error,invalid-name,broad-except
import csv
import re

from pyrevit import revit, DB
from pyrevit import script
from pyrevit import forms

__title__ = "Material from CSV"
__author__ = "{{author}}"

class MatOption(forms.TemplateListItem):

    @property
    def name(self):
        """Mat Name"""
        try:
            # return '{}: {}'.format(revit.query.get_name(self.item), revit.doc.GetElement(self.item.AppearanceAssetId).Name)
            return '[{}] {}: {}'.format(revit.doc.GetElement(self.item.AppearanceAssetId).GetRenderingAsset().Name,\
                                        revit.query.get_name(self.item),\
                                        revit.doc.GetElement(self.item.AppearanceAssetId).Name)
        except AttributeError:
            return revit.query.get_name(self.item)

def toRevitColor(color):
    r, g, b = color.split(",")
    return DB.Color(int(r), int(g), int(b))

def prop_by_name(schema_name, prop_name):
    patt = re.sub('Schema', "", schema_name)
    patt = re.sub('Prism', "Advanced", patt)

    nameSpace = DB.Visual
    schema = getattr(nameSpace, patt)
    prop = getattr(schema, prop_name)
    return prop

logger = script.get_logger()
forms.check_modeldoc(revit.doc, exitscript=True)

# make sure user is using 2019 or later
app = revit.doc.Application
if int(app.VersionNumber) < 2019:
    forms.alert('You must use Revit 2019 or newer to use this script.', exitscript=True)

# pick csv
source_file = forms.pick_file(file_ext='csv')

if source_file:
    col_mats = []
    col = DB.FilteredElementCollector(revit.doc).OfClass(DB.Material)
    for c in col:
        if revit.doc.GetElement(c.AppearanceAssetId):
            col_mats.append(c)

    col = sorted(col_mats, key=lambda x: revit.doc.GetElement(x.AppearanceAssetId).GetRenderingAsset().Name)


    selected_mat = forms.SelectFromList.show(
        {
            '*All Materials': [MatOption(x) for x in col],
            # '*SSG Materials': [MatOption(x) for x in col if 'SSG' in x.Name]            
            'Generic': [MatOption(x) for x in col if 'Generic' in revit.doc.GetElement(x.AppearanceAssetId).GetRenderingAsset().Name],            
            'Advanced Opaque': [MatOption(x) for x in col if 'PrismOpaque' in revit.doc.GetElement(x.AppearanceAssetId).GetRenderingAsset().Name],            
            'Advanced Layered': [MatOption(x) for x in col if 'PrismLayered' in revit.doc.GetElement(x.AppearanceAssetId).GetRenderingAsset().Name],            
            'Advanced Metal': [MatOption(x) for x in col if 'PrismMetal' in revit.doc.GetElement(x.AppearanceAssetId).GetRenderingAsset().Name],            
            'Advanced Transparent': [MatOption(x) for x in col if 'PrismTransparent' in revit.doc.GetElement(x.AppearanceAssetId).GetRenderingAsset().Name]            
        },
        multiselect=False,
        checked_only=True,
        button_name='Select Template Material')

    # assetElem = revit.doc.GetElement(default[0].AppearanceAssetId)

    with revit.Transaction("Create Materials"):

        with open(source_file, 'rb') as csv_file:
            csv_reader = csv.DictReader(csv_file)

            # next(csv_reader)

            for mat in csv_reader:
                # print(mat)
                mat_name = mat.pop('Name')
                if DB.Material.IsNameUnique(revit.doc, mat_name):
                    # Create Material
                    print('Creating material ' + mat_name)
                    new_mat_id = DB.Material.Create(revit.doc, mat_name)
                    new_mat = revit.doc.GetElement(new_mat_id)
                    assetElem = revit.doc.GetElement(selected_mat.AppearanceAssetId)
                    assetName = mat.pop('Asset Name')
                    duplicate_asset = assetElem.Duplicate(assetName.lower())
                    new_mat.AppearanceAssetId = duplicate_asset.Id
                    schema_name = mat.pop('Base Schema')
                else:
                    message = '"%s" already exists. Attempting to edit parameters' % mat_name
                    logger.warning(message)
                    #If it already exists, collect it and modify it
                    namePar = DB.ParameterValueProvider(DB.ElementId(DB.BuiltInParameter.MATERIAL_NAME))
                    fRule = DB.FilterStringRule(namePar, DB.FilterStringEquals(), mat_name, True)
                    filter = DB.ElementParameterFilter(fRule)
                    new_mat = DB.FilteredElementCollector(revit.doc).OfClass(DB.Material).WherePasses(filter).FirstElement()
                    assetElem = revit.doc.GetElement(new_mat.AppearanceAssetId)
                    schema_name = assetElem.GetRenderingAsset().Name
                    del mat['Base Schema']

                # ----- IDENTITY TAB -----
                # Description
                mat_description = mat.pop('Description')
                if mat_description:
                    description = new_mat.get_Parameter(DB.BuiltInParameter.ALL_MODEL_DESCRIPTION)
                    description.Set(mat_description)

                # Material Class
                mat_class = mat.pop('Class')
                if mat_class:
                    new_mat.MaterialClass = mat_class

                # Comments
                mat_comments = mat.pop('Comments')
                if mat_comments:
                    comments = new_mat.get_Parameter(DB.BuiltInParameter.ALL_MODEL_INSTANCE_COMMENTS)
                    comments.Set(mat_comments)

                # Keywords cannot be accessed through API

                # Manufacturer
                mat_mfg = mat.pop('Manufacturer')
                if mat_mfg:
                    manufacturer = new_mat.get_Parameter(DB.BuiltInParameter.ALL_MODEL_MANUFACTURER)
                    manufacturer.Set(mat_mfg)

                # Model
                mat_model = mat.pop('Model')
                if mat_model:
                    model = new_mat.get_Parameter(DB.BuiltInParameter.ALL_MODEL_MODEL)
                    model.Set(mat_model)

                # Cost
                mat_cost = mat.pop('Cost')
                if mat_cost:
                    cost = new_mat.get_Parameter(DB.BuiltInParameter.ALL_MODEL_COST)
                    cost.Set(float(mat_cost))

                # URL
                mat_url = mat.pop('URL')
                if mat_url:
                    url = new_mat.get_Parameter(DB.BuiltInParameter.ALL_MODEL_URL)
                    url.Set(mat_url)

                # Keynote
                mat_keynote = mat.pop('Keynote')
                if mat_keynote:
                    keynote = new_mat.get_Parameter(DB.BuiltInParameter.KEYNOTE_PARAM)
                    keynote.Set(mat_keynote)

                # Mark
                mat_mark = mat.pop('Mark')
                if mat_mark:
                    mark = new_mat.get_Parameter(DB.BuiltInParameter.ALL_MODEL_MARK)
                    mark.Set(mat_mark)
                
                # ----- GRAPHICS TAB -----
                # Use Render Appearance
                try:
                    use_render = bool(int(mat.pop('Use Render Appearance')))
                except ValueError:
                    print('Use Render Appearance Failed. Make sure you are using 0 or 1 values')
                if use_render:
                    use_render_app = new_mat.UseRenderAppearanceForShading 
                    use_render_app = use_render

                # Shading Color & Transparency
                shading_color = toRevitColor(mat.pop('Shading Color'))
                transparency = int(mat.pop('Transparency'))
                if not use_render:
                    if shading_color:
                        sColor = new_mat.Color
                        sColor = shading_color
                    if transparency:
                        sTransparency = new_mat.Transparency
                        sTransparency = transparency


                # ----- APPEARANCE TAB -----
                with DB.Visual.AppearanceAssetEditScope(assetElem.Document) as editScope:
                    editableAsset = editScope.Start(new_mat.AppearanceAssetId)

                    # Asset Name
                    try:
                        asset_name = mat.pop('Asset Name')
                        if asset_name:
                            asset_nm = editableAsset[DB.Visual.SchemaCommon.UIName]
                            if asset_nm.IsEditable():
                                asset_nm.Value = asset_name
                    except KeyError:
                        pass

                    # Asset Description
                    asset_description = mat.pop('Asset Description')
                    if asset_description:
                        asset_descrip = editableAsset[DB.Visual.SchemaCommon.Description]
                        asset_descrip.Value = asset_description
        
                    # Keywords
                    asset_keywords = mat.pop('Asset Keywords')
                    if asset_keywords:
                        asset_key = editableAsset[DB.Visual.SchemaCommon.Keyword]
                        if asset_key.IsEditable():
                            # asset_key.Value = asset_keywords.replace(":", ",")
                            asset_key.Value = asset_keywords


                    for k, v in mat.items():
                        prop = editableAsset[prop_by_name(schema_name, k)]
                        if prop.Type == DB.Visual.AssetPropertyType.Double4:
                            connectedAsset = prop.GetSingleConnectedAsset()
                            if len(v.split(",")) == 3:
                                if connectedAsset:
                                    prop.RemoveConnectedAsset()
                                if prop.IsValidValue(toRevitColor(v)):
                                    prop.SetValueAsColor(toRevitColor(v))
                            else:
                                # connectedAsset = prop.GetSingleConnectedAsset()
                                if not connectedAsset:
                                    prop.AddConnectedAsset('UnifiedBitmap')
                                    connectedAsset = prop.GetSingleConnectedAsset()
                                if connectedAsset:
                                    propBitmapProperty = connectedAsset['unifiedbitmap_Bitmap']
                                    # print(propBitmapProperty.Name)
                                    if propBitmapProperty.IsValidValue(v):
                                        propBitmapProperty.Value = str(v)
                                    else:
                                        print("Unable to modify {} for {}.".format(prop.Name, mat_name))
                        
                        elif prop.Type == DB.Visual.AssetPropertyType.Reference:
                            connectedAsset = prop.GetSingleConnectedAsset()
                            # print('Reference')
                            if not connectedAsset:
                                # print('no connected asset')
                                prop.AddConnectedAsset('BumpMap')
                                connectedAsset = prop.GetSingleConnectedAsset()
                            if connectedAsset:
                                propBumpmapProperty = connectedAsset['bumpmap_Bitmap']
                                if propBumpmapProperty.IsValidValue(v):
                                    propBumpmapProperty.Value = str(v)
                                else:
                                    print("Unable to modify {} for {}.".format(prop.Name, mat_name))

                        else:
                            prop.Value = v

                    
                    editScope.Commit(True)