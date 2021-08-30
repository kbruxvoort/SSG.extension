'''
from ssgutils import get_outline


class Paperspace(object):
    def __init__(self, viewSheet, views, border=0):
        # self.v_width = viewTile[0]
        # self.tile_height = viewTile[1]
        self.border = border
        self.sheet_width = get_outline(viewSheet)[0]
        self.sheet_height = get_outline(viewSheet)[1]
        self.columns = 0
        self.rows = 0
        self.tile_size = (0, 0)

    def get_max_view(self):
        widths, lengths = [], []
        for v in self.views:
            w, l = get_outline(v)
            widths.append(w)
            lengths.append(l)
        max_width, max_length = max(widths), max(lengths)
        return (max_width, max_length)

    def grid_array(self):
        max_width, max_length = self.get_max_view()
        self.columns = int(self.sheet_width / max_width)
        self.rows = int(self.sheet_length / max_length)

        tile_width = self.sheet_width / self.columns
        tile_length = self.sheet_length / self.rows

        self.tile_size = (tile_width, tile_length)
        '''


""" Partition a list into sublists whose sums don't exceed a maximum 
    using a First Fit Decreasing algorithm. See
    http://www.ams.org/new-in-math/cover/bins1.html
    for a simple description of the method.
"""


class Bin(object):
    """ Container for items that keeps a running sum """

    def __init__(self):
        self.items = []
        self.sum = 0

    def append(self, item):
        self.items.append(item)
        self.sum += item

    def __str__(self):
        """ Printable representation """
        return "Bin(sum=%d, items=%s)" % (self.sum, str(self.items))

class InsertPoint(object):
    def __init__(self):


def pack(values, maxValue):
    values = sorted(values, reverse=True)
    bins = []

    for item in values:
        # Try to fit item into a bin
        for bin in bins:
            if bin.sum + item <= maxValue:
                # print 'Adding', item, 'to', bin
                bin.append(item)
                break
        else:
            # item didn't fit into any bin, start a new bin
            # print 'Making new bin for', item
            bin = Bin()
            bin.append(item)
            bins.append(bin)

    return bins


if __name__ == "__main__":
    import random

    def packAndShow(aList, maxValue):
        """ Pack a list into bins and show the result """
        print "List with sum", sum(aList), "requires at least", (
            sum(aList) + maxValue - 1
        ) / maxValue, "bins"

        bins = pack(aList, maxValue)

        print "Solution using", len(bins), "bins:"
        for bin in bins:
            print bin

        print

    aList = [10, 9, 8, 7, 6, 5, 4, 3, 2, 1]
    packAndShow(aList, 11)

    aList = [random.randint(1, 11) for i in range(100)]
    packAndShow(aList, 11)