import bpy
import time
from .utils.registration import *


# Check if addon is being reloaded
# This also allows script.reload() to reload the addon
if "operator_sync_view" not in locals():
    from . import sync_handler, ui, operator_sync_view, msgbus
else:
    import importlib
    sync_handler = importlib.reload(sync_handler)
    ui = importlib.reload(ui)
    operator_sync_view = importlib.reload(operator_sync_view)
    msgbus = importlib.reload(msgbus)

modules = [operator_sync_view, msgbus, ui]

bl_info = {
    "name": "Viewport Sync",
    "author": "Bowen Wu",
    "description": "Syncs specified viewports to have the same views",
    "blender": (2, 80, 3),
    "version": (0, 1, 0),
    "location": "View3D > Header Bar",
    "warning": "",
    "category": "3D View"
}


def register():
    for module in modules:
        module.register()


def unregister():
    for module in modules[::-1]:
        module.unregister()
