# from random import randint

from pyrevit import script

output = script.get_output()
# data = []
# for i in range(4):
#     data.append([randint(0, 100),randint(0, 100), randint(0, 100), randint(0, 100)])

# # data = [
# #     ['Col 1', 'Col 2', 'Col 3', 80],
# #     ['Col 4', 'Col 5', 'Col 6', 80],
# #     ['Col 7', 'Col 8', 'Col 9', 80],
# #     ['Col 10', 'Col 11', 'Col 12', 80],
# # ]

# # formats contains formatting strings for each column
# # last_line_style contains css styling code for the last line
# output.set_font("Times New Roman", 24)
# output.set_width(1920)
# output.print_table(table_data=data,
#                    title='Table',
#                    columns=['Col 1', 'Col 2', 'Col 3', "Percentage"],
#                    formats=['', '', '', '{}%'],
#                    last_line_style='color:red;')


# get line chart object
chart = output.make_line_chart()

# this is a list of labels for the X axis of the line graph
chart.data.labels = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']

# Let's add the first dataset to the chart object
# we'll give it a name: set_a
set_a = chart.data.new_dataset('set_a')

# And let's add data to it.
# These are the data for the Y axis of the graph
# The data length should match the length of data for the X axis
set_a.data = [12, 19, 3, 17, 6, 3, 7]

# Set the color for this graph
set_a.set_color(0xFF, 0x8C, 0x8D, 0.8)



# Same as above for a new data set: set_b
set_b = chart.data.new_dataset('set_b')

# You can also set custom options for this graph
# See the Charts.js documentation for all the options
set_b.fill = False

# Obviously a different set of data and a different color
set_b.data = [2, 29, 5, 5, 2, 3, 10]
set_b.set_color(0xFF, 0xCE, 0x56, 0.8)

# Same as above for a new data set: set_c
set_c = chart.data.new_dataset('set_c')

# Obviously a different set of data and a different colorset_c.data = [55, 12, 2, 20, 18, 6, 22]
set_c.set_color(0x36, 0xA2, 0xEB, 0.8)

chart.draw()