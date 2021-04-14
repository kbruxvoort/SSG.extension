import typing

"""
2D Item class.
"""
class Item:
    """
    Items class for rectangles inserted into sheets
    """
    def __init__(self, width, height, CornerPoint):
        self.width = width
        self.height = height
        self.x = CornerPoint[0]
        self.y = CornerPoint[1]
        self.area = self.width * self.height
        # self.rotated = False
        # self.id = 0


    def __repr__(self):
        return 'Item(width=%r, height=%r, x=%r, y=%r)' % (self.width, self.height, self.x, self.y)


    # def rotate(self) -> None:
    #     self.width, self.height = self.height, self.width
    #     self.rotated = False if self.rotated == True else True

class FreeRectangle(typing.NamedTuple('FreeRectangle', [('width', float), ('height', float), ('x', float), ('y', float)])):
    __slots__ = ()
    @property
    def area(self):
        return self.width*self.height

class MaximalRectangle:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.area = self.x * self.y
        self.free_area = self.area
        self.freerects = [FreeRectangle(self.x, self.y, 0, 0)]
        self.items = []

    def __repr__(self) -> str:
        return "MaximalRectangle(%r)" % (self.items)

    @staticmethod
    def _item_fits_rect(item, rect):
        if item.width <= rect.width and item.height <= rect.height):
            return True
        else:
            return False

    @staticmethod
    def _split_rectangle(rect, item):
        """
        Return a list of maximal free rectangles from a split
        """
        results = []
        if item.width < rectangle.width:
            Fw = rectangle.width - item.width
            Fh = rectangle.height
            Fx = rectangle.x + item.width
            Fy = rectangle.y
            results.append(FreeRectangle(width=Fw,
                                         height=Fh,
                                         x=Fx,
                                         y=Fy))
        if item.height < rectangle.height:
            Fw = rectangle.width
            Fh = rectangle.height - item.height
            Fx = rectangle.x 
            Fy = rectangle.y + item.height
            results.append(FreeRectangle(width=Fw,
                                         height=Fh,
                                         x=Fx,
                                         y=Fy))
        return results

    @staticmethod
    def _item_bounds(item):
        """
        Returns the lower left and upper right 
        corners of the item's bounding box.
        """
        return (item.x,
                item.y,
                item.x+item.width,
                item.y+item.height)