import bpy
from .utils import registration


def viewport_sync_button(self, context):
    layout = self.layout
    view_region = context.area.spaces[0].region_3d
    # Disable if in quadview
    if len(context.space_data.region_quadviews) <= 1:
        layout.prop(view_region, "show_sync_view", text="", icon_only=True, icon="UV_SYNC_SELECT")


class SyncViewPanel(bpy.types.Panel):
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'View'


class SYNC_VIEWVIEW3D_PT_setting_panel(SyncViewPanel):
    """Settings for Sync View"""
    bl_label = "Sync View Panel"
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout
        preferences = bpy.context.preferences.addons[__package__].preferences
        view_region = context.area.spaces[0].region_3d
        # Disable if in quadview
        if len(context.space_data.region_quadviews) <= 1:
            layout.prop(view_region, "show_sync_view", text="Sync This Viewport", icon_only=True, icon="UV_SYNC_SELECT")

        layout.label(text="Shortcuts")
        layout.operator(operator="syncview.sync_all_visible")
        layout.operator(operator="syncview.stop_sync_all_visible")

        layout.label(text="Settings")
        column = layout.column()
        column.prop(preferences, "pause_sync", icon='PAUSE')
        column.prop(preferences, "sync_playback", icon='PLAY')
        column.prop(preferences, "sync_camera_view", icon='VIEW_CAMERA')


class SYNC_VIEWVIEW3D_PT_sync_mode_panel(SyncViewPanel):
    """Settings for Sync View"""
    bl_label = "Sync Mode"
    bl_parent_id = "SYNC_VIEWVIEW3D_PT_setting_panel"
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout
        preferences = bpy.context.preferences.addons[__package__].preferences

        box = layout.box()
        box.props_enum(preferences, "sync_mode")


ui = [SYNC_VIEWVIEW3D_PT_setting_panel, SYNC_VIEWVIEW3D_PT_sync_mode_panel]


def register():
    bpy.types.VIEW3D_HT_header.append(viewport_sync_button)
    registration.register_classes(ui)


def unregister():
    bpy.types.VIEW3D_HT_header.remove(viewport_sync_button)
    registration.unregister_classes(ui)
