import bpy
from bpy.app.handlers import persistent
from . import msgbus


@persistent
def post_load_handler(dummy):
    bpy.ops.syncview.syncview_enable_sync()
    msgbus.register()


@persistent
def pre_load_handler(dummy):
    msgbus.unregister()
    bpy.ops.syncview.syncview_disable_sync()


def register():
    bpy.app.handlers.load_pre.append(pre_load_handler)
    bpy.app.handlers.load_post.append(post_load_handler)


def unregister():
    bpy.app.handlers.load_post.remove(post_load_handler)
    bpy.app.handlers.load_pre.remove(pre_load_handler)
