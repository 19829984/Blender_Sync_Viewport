import bpy
from bpy.types import AddonPreferences
from bpy.props import EnumProperty


class SyncViewPreferences(AddonPreferences):
    bl_idname = __package__

    sync_modes = {
        'Window': 0,
        'Workspace': 1,
        'All': 2
    }

    def enum_update(self, context):
        if 'view_sync' in bpy.app.driver_namespace:
            bpy.app.driver_namespace['view_sync'].build_space_map()

    sync_mode: EnumProperty(
        name="Sync Mode",
        items=[
            ('Window', 'Sync Window', 'Sync viewports within the same window', 'WINDOW', 0),
            ('Workspace', 'Sync Workspace', 'Sync viewports within the same workspace', 'WORKSPACE', 1),
            ('All', 'Sync All', 'Sync all viewports in the blend file', 'FILE_BLEND', 2)
        ],
        description="Determines what viewports to sync",
        default=0,
        update=enum_update
    )

    def draw(self, context):
        layout = self.layout
        layout.props_enum(self, "sync_mode")


def register():
    bpy.utils.register_class(SyncViewPreferences)


def unregister():
    bpy.utils.unregister_class(SyncViewPreferences)
