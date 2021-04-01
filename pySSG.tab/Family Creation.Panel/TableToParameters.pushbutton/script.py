from ast import literal_eval
from csv import DictReader, QUOTE_NONE

from pyrevit import revit, DB, script, forms
from operator import itemgetter
from rpw.ui.forms import (FlexForm, Label, ComboBox, TextBox, TextBox,
                          Separator, Button, CheckBox, Alert)

output = script.get_output()
data_types = {
    'length':['width', 'depth', 'height', 'length', 'thickness', 'offset', 'zw', 'zd', 'zh'],
    'integer':['number', 'qty', 'total'],
    'bool':['add', 'modify', 'starter', 'adder', 'vis', 'viz', 'zb']
    }

value_matches = {
    'price':['price', 'list', 'cost'],
    'model':['model', 'code']
    }

# standard_size_params = ['STD_Widths', 'STD_Depths', 'STD_Heights']

def csv_data(filepath, **matches):
    def parse_value(key, value):
        if key in matches:
            return matches[key](value)
        try:
            # Interpret the string as a Python literal
            return literal_eval(value)
        except Exception:
            # If that doesn't work, assume it's an unquoted string
            return value
    
    with open(source_file, 'rb') as csv_file:
        for row in DictReader(csv_file, quoting=QUOTE_NONE):
            yield {k: parse_value(k, v) for k, v in row.iteritems()}


# ensure active document is a family document
forms.check_familydoc(revit.doc, exitscript=True)

components = [Label('Choose Parameters'), 
            CheckBox('checkbox1', 'Price', default=True),
            CheckBox('checkbox2', 'Weight'),
            CheckBox('checkbox3', 'Product Code'),
            # Separator(),
            # Label('Dimensions'), 
            # CheckBox('checkbox4', 'Standard Sizes'),
            # CheckBox('checkbox5', 'Min & Max Sizes'),
            Button('Select')]

form = FlexForm('CSV to Formulas', components)

if form.show():
    priceChecked = form.values['checkbox1']
    weightChecked = form.values['checkbox2']
    codeChecked = form.values['checkbox3']
    # standardChecked = form.values['checkbox4']
    # minMaxChecked = form.values['checkbox5']

    # pick csv
    source_file = forms.pick_file(file_ext='csv')

    if source_file:
        # csv_reader = list(csv_data(source_file, ACTUAL_Width=float))
        csv_reader = list(csv_data(source_file))
        field_names = [x for x in csv_reader[0]]
        formula_cols = field_names[:]
        for n in field_names:

            if any(word in n.replace("_", " ").lower() for word in value_matches['model']):
                model_name = n

            elif any(word in n.replace("_", " ").lower() for word in value_matches['price']):
                price_name = n

            elif any(word in n.replace("_", " ").lower() for word in ['weight']):
                weight_name = n

 
        formula_cols.remove(model_name)
        formula_cols.remove(price_name)
        formula_cols.remove(weight_name)

        # create an empty list for each column so that we can get a list of unique values
        header_lst = [[] for i in range(len(formula_cols))]
        model_lst, price_lst, weight_lst = [], [], []
        count = 0
        # csv_reader = sorted(csv_reader, key=lambda i: i['ACTUAL_Width'] )
        csv_reader = sorted(csv_reader, key=itemgetter(*formula_cols), reverse=True)

        # get unique values of each column. using a list instead of a set because we need to maintain the order
        for row in csv_reader:
            # print(row)
            for c, h in zip(formula_cols, header_lst):
                if row[c] not in h:
                    h.append(row[c])

        # loop through again to create formula
        empty_line = False
        for row in csv_reader:
            lst = []
            formula = ''
            param_count = 0
            expression = ''
            for i, c in enumerate(formula_cols):
                # checking the column names to see if they have length terms. 
                # If they do, we use ">" to create a range instead of "="
                if any(term in c.lower() for term in data_types['length']):

                    try:
                        # if we are using a range we say ">" the next value in the set
                        value = header_lst[i][header_lst[i].index(row[c])+1]
                        expression += c + " > " + str(value) + "\", "
                        param_count += 1

                    except IndexError:
                        # An index error means we have gotten to the last item in the list
                        # We can set the value as the false
                        pass
                
                elif any(term in c.lower() for term in data_types['bool']):
                    if row[c] == True:
                        expression += c + ", "
                        param_count += 1

                else:
                    # if value is the last one in the unique values we can treat it as the false
                    if row[c] != header_lst[i][-1]:
                        expression += c + " = " + str(row[c]) + ", "
                        param_count += 1

            model, price, weight = '"' + str(row[model_name]) + '"', str(row[price_name]), str(row[weight_name])

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
                if p.Definition.Name not in formula_cols:
                    param_dict[p.Definition.Name] = p

                # elif p.Definition.Name in standard_size_params:
                #     param_dict[p.Definition.Name] = p

            if priceChecked:
                output.print_code(price_formula)
                revit.doc.FamilyManager.SetFormula(param_dict[price_name], price_formula)
                
            if weightChecked:
                output.print_code(weight_formula)
                revit.doc.FamilyManager.SetFormula(param_dict[weight_name], weight_formula)

            if codeChecked:
                output.print_code(model_formula)
                revit.doc.FamilyManager.SetFormula(param_dict[model_name], model_formula)


        
