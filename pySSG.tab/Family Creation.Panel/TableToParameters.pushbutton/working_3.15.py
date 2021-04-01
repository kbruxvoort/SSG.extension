import csv

from pyrevit import revit, DB, script, forms
from operator import itemgetter
from rpw.ui.forms import (FlexForm, Label, ComboBox, TextBox, TextBox,
                          Separator, Button, CheckBox, Alert)

output = script.get_output()
dim_terms = ['width', 'depth', 'height', 'length']
bool_terms = ['add', 'modify', 'starter', 'adder', 'vis', 'viz']
standard_size_params = ['STD_Widths', 'STD_Depths', 'STD_Heights']


# ensure active document is a family document
forms.check_familydoc(revit.doc, exitscript=True)

components = [Label('Choose Parameters'), 
            CheckBox('checkbox1', 'Price', default=True),
            CheckBox('checkbox2', 'Weight', default=True),
            CheckBox('checkbox3', 'Product Code'),
            Separator(),
            Label('Dimensions'), 
            CheckBox('checkbox4', 'Standard Sizes'),
            CheckBox('checkbox5', 'Min & Max Sizes'),
            Button('Select')]

form = FlexForm('CSV to Formulas', components)

if form.show():
    priceChecked = form.values['checkbox1']
    weightChecked = form.values['checkbox2']
    codeChecked = form.values['checkbox3']
    standardChecked = form.values['checkbox4']
    minMaxChecked = form.values['checkbox5']

    # pick csv
    source_file = forms.pick_file(file_ext='csv')

    if source_file:
        with open(source_file, 'rb') as csv_file:
                csv_reader = csv.DictReader(csv_file, quoting=csv.QUOTE_NONNUMERIC, dialect="excel")
                headers = csv_reader.fieldnames
                cols = headers[1:-2]
                clean_headers = [x.replace('"', '') for x in headers]
                
                # model_name = headers[0].replace('"', '')
                # price_name = headers[-2].replace('"', '')
                # weight_name = headers[-1].replace('"', '')
                model_name = clean_headers[0]
                price_name = clean_headers[-2]
                weight_name = clean_headers[-1]

                # create an empty list for each column so that we can get a list of unique values
                header_lst = [[] for i in range(len(cols))]

                model_lst, price_lst, weight_lst = [], [], []

                count = 0
                csv_reader = sorted(csv_reader, key=itemgetter(*cols), reverse=True)

                # get unique values of each column. using a list instead of a set because we need to maintain the order
                for row in csv_reader:
                    for c, h in zip(cols, header_lst):
                        if row[c] not in h:
                            h.append(row[c])

                # loop through again to create formula
                empty_line = False
                for row in csv_reader:
                    lst = []
                    formula = ''
                    param_count = 0
                    expression = ''
                    for i, c in enumerate(cols):
                        # checking the column names to see if they have length terms. 
                        # If they do, we use ">" to create a range instead of "="
                        if any(term in c.replace("_", " ").lower() for term in dim_terms):

                            try:
                                # if we are using a range we say ">" the next value in the set
                                value = header_lst[i][header_lst[i].index(row[c])+1]
                                expression += c.replace('"', '') + " > " + str(value) + "\", "
                                param_count += 1

                            except IndexError:
                                # An index error means we have gotten to the last item in the list
                                # We can set the value as the false
                                pass
                        
                        elif any(term in c.replace("_", " ").lower() for term in bool_terms):
                            if row[c].lower() == '"yes"':
                                expression += c.replace('"', '') + ", "
                                param_count += 1

                        else:
                            # if value is the last one in the unique values we can treat it as the false
                            if row[c] != header_lst[i][-1]:
                                expression += c.replace('"', '') + " = " + str(row[c]) + ", "
                                param_count += 1

                    # these columns are predetermined to make finding the correct data easier 
                    model, price, weight = str(row[headers[0]]), str(row[headers[-2]]), str(row[headers[-1]])

                    # the number of expressions determines how each line is written
                    # if there are multiple expressions we need the "and" operator
                    if param_count > 1:
                        formula += "if(and(" + expression.rstrip(", ") + "), "
                    # if there is one expression we just need "if"
                    elif param_count > 0:
                        formula += "if(" + expression
                    # if there are NO expressions that means the last line is empty
                    # We set empty_line to True so we know not to add a False to the end of the formula
                    else:
                        empty_line = True
                    
                    # x = "if(and(" + ", ".join(lst) + "), "
                    
                    model_lst.append(formula + model)
                    price_lst.append(formula + price)
                    weight_lst.append(formula + weight)
                    count += 1
                
                model_formula = ",\n".join(model_lst)
                price_formula = ",\n".join(price_lst)
                weight_formula = ",\n".join(weight_lst)

                if empty_line:
                    model_formula = model_formula + ")" * (count - 1)
                    price_formula = price_formula + ")" * (count - 1)
                    weight_formula = weight_formula + ")" * (count - 1)
                
                else:
                    model_formula = model_formula + ', "NA"' + ')' * count
                    price_formula = price_formula + ", 0" + ")" * count
                    weight_formula = weight_formula + ", 0" + ")" * count

    
        with revit.Transaction('Set Formulas'):
            fam_params = revit.doc.FamilyManager.GetParameters()
            
            param_dict = {}
            for p in fam_params:
                if p.Definition.Name in clean_headers and p.Definition.Name not in cols:
                    param_dict[p.Definition.Name] = p

                elif p.Definition.Name in standard_size_params:
                    param_dict[p.Definition.Name] = p

            if priceChecked:
                revit.doc.FamilyManager.SetFormula(param_dict[price_name], price_formula)
                output.print_code(price_formula)

            if weightChecked:
                revit.doc.FamilyManager.SetFormula(param_dict[weight_name], weight_formula)
                output.print_code(weight_formula)

            if codeChecked:
                revit.doc.FamilyManager.SetFormula(param_dict[model_name], model_formula)
                output.print_code(model_formula)
                '''
                if standardChecked:
                if minMaxChecked:
                
                if p.Definition.Name == model_name:
                    revit.doc.FamilyManager.SetFormula(p, model_formula)

                elif p.Definition.Name == price_name:
                    revit.doc.FamilyManager.SetFormula(p, price_formula)

                elif p.Definition.Name == weight_name:
                    revit.doc.FamilyManager.SetFormula(p, weight_formula)
                    '''
