from pyrevit import script

output = script.get_output()

# get radar chart object
chart = output.make_radar_chart()

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
# set_b.fill = False

# Obviously a different set of data and a different color
set_b.data = [2, 29, 5, 5, 2, 3, 10]
set_b.set_color(0xFF, 0xCE, 0x56, 0.8)

# Same as above for a new data set: set_c
set_c = chart.data.new_dataset('set_c')

# Obviously a different set of data and a different colorset
set_c.data = [55, 12, 2, 20, 18, 6, 22]
set_c.set_color(0x36, 0xA2, 0xEB, 0.8)

# Finally let's draw the chart
chart.draw()
