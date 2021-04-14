import random

class Node(object):
    def __init__(self, w, h):
        # self.root = {"x": 0, "y": 0, "w": w, "h": h}
        self.x = 0
        self.y = 0
        self.w = w
        self.h = h
        self.used = False
        self.right = None
        self.down = None
        self.root = {"x": self.x, "y": self.y, "w": self.w, "h": self.h}

    def __repr__(self):
        return '({}, {})'.format(self.root['w'], self.root['h'])

    def fit(self, blocks):
        for b in blocks:
            node = self.findNode(self.root, b.w, b.h)
            if node:
                b.fit = self.splitNode(node, b.w, b.h)

    def findNode(self, root, w, h):
        if root.used:
            return self.findNode(root.right, w, h) or self.findNode(root.down, w, h)
        elif w <= root.w and h <= root.h:
            return root
        else:
            return None

    def splitNode(self, node, w, h):
        node.used = True
        node.down = {"x": node.x, "y": node.y + h, "w": node.w, "h": node.h - h}
        node.right = {"x": node.x + w, "y": node.y, "w": node.w - w, "h": h}
        return node


    


views = []
for i in range(10):
    views.append(Node(random.randint(1, 5), random.randint(2, 4)))

views = sorted(views, key=lambda x: (x.root['w'], x.root['h']), reverse=True)

print(repr(views))

container = Node(7.5, 8.5)
print(container.fit(views))


# for v in views:
#     if v.w <= root.w and v.h <= root.h:
#         # 

