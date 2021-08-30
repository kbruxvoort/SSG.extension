from pyrevit import revit, DB

# from ssgutils import get_rectangle
# from packer import Packer

from pyrevit import forms

forms.inform_wip()

# top_border = 1.5
# side_border = 0.5
# bot_border = 1.0

# collector = DB.FilteredElementCollector(revit.doc)
# collector.OfClass(DB.ViewPlan).ToElements()
# mat_views = []
# for c in collector:
#     if not c.IsTemplate and "SSG" in c.Name:
#         w, l = get_rectangle(c)
#         mat_views.append(c)
#         # print((c.ViewName, w*12, l*12))

# selection = revit.get_selection()
# for s in selection:
#     width, height = get_rectangle(s)
#     print('{}: {}"W x {}"H'.format(s.Name, width*12, height*12))
#     P1 = DB.XYZ(side_border/12.0, height - top_border/12.0, 0)
#     print('Start point: {}'.format(P1))
#     paper_space_width = width - side_border * 2 / 12
#     paper_space_height = height - top_border / 12 - bot_border / 12
#     ps = Packer(0, 0, paper_space_width, paper_space_height)

#     print('Usable space: {}"W x {}"H'.format(paper_space_width*12, paper_space_height*12))


#     mat_views = sorted(mat_views, key=lambda v: get_rectangle(v)[1], reverse=True)
#     test = ps.fit(mat_views)
