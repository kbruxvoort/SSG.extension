#! python3


# set PYTHONPATH to ....\Lib\site-packages correctly
# import sys
# sys.path.append(r'C:\Python38\Lib\site-packages')

# import wx
import pandas as pd


def print_html(output_str):
    print(output_str.replace("<", "&clt;").replace(">", "&cgt;"))


"""
if forms.check_familydoc():
    # pick csv
    source_file = forms.pick_file(file_ext='csv')

    if source_file:
        with open(source_file, 'rb') as csv_file:
            csv_reader = csv.DictReader(csv_file)
            headers = csv_reader.fieldnames
            print(headers)
            for row in csv_reader:
                print(row)
                """


# if forms.check_familydoc():
#     # pick csv
#     source_file = forms.pick_file(file_ext="csv")


df = pd.read_csv(r"D:\Desktop\SSG_Cabinet_Base_1_Door_1_Drawer_LAM.csv")
print_html(df.to_html().replace("\n", ""))
