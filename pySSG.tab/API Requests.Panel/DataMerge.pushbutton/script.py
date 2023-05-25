# -*- coding: utf-8 -*-

import os
import csv
import io

import requests

from pyrevit import forms
from fetch_client import Client, get_auth

    
class FamilyOption(forms.TemplateListItem):
    @property
    def name(self):
        return self.item["Name"]
    

bim_key = get_auth()

if bim_key:

    headers = {
        "Authorization": "Bearer {}".format(bim_key),
        "Accept": "application/json",
        "Content-Type": "application/json",
    }
    s = requests.Session()
    s.headers.update(headers)

    search_text = forms.ask_for_string(
        title="Family Search",
        prompt="Input search string to find families"
    )
    
    fetch = Client(auth=bim_key)
    if search_text:

        params = {
            "SearchText": "{}".format(search_text)
        }
        r = s.post("https://www.ssgbim.com/webapi/Search/Families", params=params)
        r.raise_for_status()
        results = r.json().get('BusinessFamilies')
        
        if results:
            selection = forms.SelectFromList.show(
                [FamilyOption(f) for f in results],
                multiselect=True,
            )
            if selection:
                directory = forms.pick_folder()
                if directory:
                    new_path = directory + "\\images"
                    if not os.path.exists(new_path):
                        os.makedirs(new_path)
                    if not isinstance(selection, list):
                        selection = [selection]


                    results = []
                    for sel in selection:
                        print(sel.get('Name'))
                        _id = sel.get('Id')
                        response = fetch.families.retrieve(_id)
                        if response:
                            results.append(response)
                            
                        table_response = fetch.families.get_table(_id)
                        if table_response:
                            file_directory = directory + "\\price_tables"
                            if not os.path.exists(file_directory):
                                os.makedirs(file_directory)
                            filename = "price_table_" + sel.get('Name') + ".csv"
                            filepath = os.path.join(file_directory, filename)
                            
                            with open(filepath, 'wb') as file:
                                file.write(table_response)

                    
                    if results:
                        image_urls = []    
                        with io.open(directory + '\\data_merge.csv', 'w', encoding='utf-8', newline='') as new_file:
                            fieldnames = [
                                "@image", 
                                "header", 
                                "subheader", 
                                "masterformat", 
                                "uniformat", 
                                "omniclass", 
                                "detail_1", 
                                "detail_2", 
                                "detail_3", 
                                "detail_4", 
                                "description"
                            ]

                            
                            csv_writer = csv.DictWriter(new_file, fieldnames=fieldnames)
                            csv_writer.writeheader()
                            for res in results:
                                files = res.get('Files')
                                props = res.get('Properties')
                                params = res.get('Parameters')
                                
                                
                                
                                large_images = [f['FileNameWithExtension'] for f in res['Files'] if f['FileKey'] == 'FamilyImageLarge']
                                if large_images:
                                    header = [p['Value'] for p in props if p['Name'] == 'TitleHeader']
                                    subheader = [p['Value'] for p in props if p['Name'] == 'TitleSubheader']
                                    detail = [p['Value'].encode('ascii', 'ignore') for p in props if p['Name'] == 'Detail']
                                    description = [p['Value'].encode('ascii', 'ignore') for p in params if p['Name'] == 'SSG_Long Description']
                                    masterformat = [p['Value'] for p in params if p['Name'] == 'Keynote']
                                    uniformat = [p['Value'] for p in params if p['Name'] == 'Assembly Code']
                                    omniclass = [p['Value'] for p in params if p['Name'] == 'Omniclass']
                                    
                                    if detail:
                                        detail = detail[0].replace("<ul><li>", "").replace("</li></ul>", "").split("</li><li>")

                                    detail_iter = iter(detail)

                                    fam_dict = {
                                        "@image": "\\images\\{}".format(next(iter(large_images), None)),
                                        "header": next(iter(header), ""),
                                        "subheader": next(iter(subheader), ""),
                                        "masterformat": next(iter(masterformat), ""),
                                        "uniformat": next(iter(uniformat), ""),
                                        "omniclass": next(iter(omniclass), ""),
                                        "detail_1": next(detail_iter, ""),
                                        "detail_2": next(detail_iter, ""),
                                        "detail_3": next(detail_iter, ""),
                                        "detail_4": next(detail_iter, ""),
                                        "description": next(iter(description), "")
                                    }

                                    csv_writer.writerow(fam_dict)
                                    url = "https://www.ssgbim.com/Family/{}/File/FamilyImageLarge".format(res['Id'])
                                    full_path = "{}\\{}".format(new_path, next(iter(large_images), None))
                                    image_urls.append((url, full_path))
                                    
                        for url, full_path in image_urls:
                            image = s.get(url, stream=True)
                            with open(full_path, 'wb') as f:
                                for chunk in image:
                                    f.write(chunk)
        else:
            forms.alert(msg="No results found", exitscript=True)
else:
    forms.alert(msg="Missing token in environment variables", exitscript=True)
