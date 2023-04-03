import bpy
import os


def register_classes(classes):
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister_classes(classes):
    for cls in classes[::-1]:
        bpy.utils.unregister_class(cls)

# def register_icons(paths):
#     global custom_icons
#     custom_icons = bpy.utils.previews.new()
#     icons_dir = os.path.join(os.path.dirname(__file__), "icons")

#     for path in paths:
#         custom_icons.load()
