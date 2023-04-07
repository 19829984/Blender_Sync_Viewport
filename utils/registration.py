import bpy


def register_classes(classes):
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister_classes(classes):
    for cls in classes[::-1]:
        bpy.utils.unregister_class(cls)
