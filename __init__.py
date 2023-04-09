# Check if addon is being reloaded
# This also allows script.reload() to reload the addon
if "operator_sync_view" not in locals():
    from . import sync_handler, ui, operator_sync_view, msgbus, preferences, handlers
else:
    import importlib
    sync_handler = importlib.reload(sync_handler)
    ui = importlib.reload(ui)
    operator_sync_view = importlib.reload(operator_sync_view)
    msgbus = importlib.reload(msgbus)
    preferences = importlib.reload(preferences)
    handlers = importlib.reload(handlers)

modules = [preferences, operator_sync_view, ui, handlers, msgbus]

bl_info = {
    "name": "Viewport Sync",
    "author": "Bowen Wu",
    "description": "Syncs specified viewports to have the same views",
    "blender": (2, 80, 3),
    "version": (1, 0, 2),
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
