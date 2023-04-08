import bpy
from bpy.types import AddonPreferences
from bpy.props import EnumProperty, BoolProperty


class SyncViewPreferences(AddonPreferences):
    bl_idname = __package__

    sync_modes = {
        "Window": 0,
        "Workspace": 1,
        "All": 2
    }

    def enum_update(self, context):
        if 'sync_view' in bpy.app.driver_namespace:
            bpy.app.driver_namespace['sync_view'].build_map()

    sync_mode: EnumProperty(
        name="Sync Mode",
        items=[
            ("Window", "Sync Window", "Sync viewports within the same window", 'WINDOW', 0),
            ("Workspace", "Sync Workspace", "Sync viewports within the same workspace", 'WORKSPACE', 1),
            ("All", "Sync All", "Sync all viewports in the blend file", 'FILE_BLEND', 2)
        ],
        description="Determines what viewports to sync",
        default=0,
        update=enum_update
    )

    pause_sync: BoolProperty(
        name="Pause Sync",
        description="Temporarily Pause Sync",
        default=False,
    )

    sync_playback: BoolProperty(
        name="Sync Playback",
        description="Sync During Playback",
        default=True,
    )

    sync_camera_view: BoolProperty(
        name="Sync Camera View",
        description="Sync Viewports in Camera View",
        default=True,
    )

    def draw(self, context):
        layout = self.layout
        layout.props_enum(self, "sync_mode")
        row = layout.row()
        row.prop(self, "pause_sync")
        row.prop(self, "sync_playback")
        row.prop(self, "sync_camera_view")


def register():
    bpy.utils.register_class(SyncViewPreferences)


def unregister():
    bpy.utils.unregister_class(SyncViewPreferences)
