class Packer(object):
    def __init__(self, w, h, pt_x, pt_y):
        self.w = w
        self.h = h
        self.x = pt_x
        self.y = pt_y
        self.area = self.w * self.h
        self.root = Packer(self.w, self.h, 0, 0)

# class Node(Packer):
#     def __init__(self, w, h)
#         super().__init__(w, h)
#         self.root = Packer(w, h)

# class Node(object):
#     def __init__(self, x, y, w, h):
#         self.w = w
#         self.h = h
#         self.x = x
#         self.y = y
#         self.right = None
#         self.down = None
#         self.isOccupied = None
#         self.root = Node(0, 0, w, h)

    def fit(self, blocks):
        for b in blocks:
            node = self.findNode(self.root, b.w, b.h)
            if node:
                b.fit = self.splitNode(node, b.w, b.h)
                print(b.fit)

    def findNode(self, root, w, h):
        if root.isOccupied:
            return self.findNode(root.right, w, h) or self.findNode(root.down, w, h)
        elif w <= root.w and h <= root.h:
            return root
        else:
            return None

    
    def splitNode(self, node, w, h):
        node.isOccupied = True
        node.down = Packer(node.x, node.y + h, node.w, node.h - h)
        node.right = Packer(node.x + w, node.y, node.w - w, h)
        return node