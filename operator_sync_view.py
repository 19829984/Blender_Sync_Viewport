import bpy
from .sync_handler import SyncDrawHandler
from .utils.registration import register_classes, unregister_classes
import logging


class SYNC_VIEW_EVENTKEYMAP_OT_mouse_move(bpy.types.Operator):
    """
    This operator reports the active area to our draw handler, is meant to be called through a keymap on mouse move
    Adapted from https://blender.stackexchange.com/questions/267285/alternative-to-modal-operators-blocked-autosave
    """
    bl_idname = "syncview.report_active_area"
    bl_label = "Report Active Area"

    @classmethod
    def poll(cls, context):
        return context and context.area

    def execute(self, context: bpy.types.Context):
        if 'sync_view' in bpy.app.driver_namespace:
            sync_view = bpy.app.driver_namespace['sync_view']
            sync_view.active_space = context.area.spaces.active
            sync_view.active_window = context.window

        return {'PASS_THROUGH'}

    def invoke(self, context: bpy.types.Context, event: bpy.types.Event):
        return self.execute(context)


class SYNC_VIEW_OT_EnableSync(bpy.types.Operator):
    """Enable sync view by initializing its draw handler callback"""
    bl_idname = "syncview.syncview_enable_sync"
    bl_label = "Enable Sync View Operator"

    @classmethod
    def poll(cls, context):
        return bpy.app.driver_namespace

    def execute(self, context):
        driver_namespace = bpy.app.driver_namespace
        if 'sync_view' not in driver_namespace:
            logger = logging.getLogger(__name__ + ".SYNC_VIEWOT_EnableSync")
            logger.info("Adding SyncDrawHandler to driver_namespace['sync_view']")
            driver_namespace['sync_view'] = SyncDrawHandler()

        return {'FINISHED'}

    def invoke(self, context: bpy.types.Context, event: bpy.types.Event):
        return self.execute(context)


class SYNC_VIEW_OT_DisableSync(bpy.types.Operator):
    """Disable sync view by removing its draw handler callback"""
    bl_idname = "syncview.syncview_disable_sync"
    bl_label = "Disable Sync View Operator"

    @classmethod
    def poll(cls, context):
        return bpy.app.driver_namespace

    def execute(self, context):
        driver_namespace = bpy.app.driver_namespace
        if 'sync_view' in driver_namespace and driver_namespace['sync_view'].has_handler():
            logger = logging.getLogger(__name__ + ".SYNC_VIEW_OT_DisableSync")
            logger.info("Removing SyncDrawHandler to driver_namespace['sync_view']")
            del bpy.app.driver_namespace['sync_view']

        return {'FINISHED'}

    def invoke(self, context: bpy.types.Context, event: bpy.types.Event):
        return self.execute(context)


class SYNC_VIEW_OT_SyncAllVisible(bpy.types.Operator):
    """Sync all visible viewports"""
    bl_idname = "syncview.sync_all_visible"
    bl_label = "Sync All Visible"

    @classmethod
    def poll(cls, context):
        return context.region_data

    def execute(self, context):
        for window in context.window_manager.windows:
            for area in window.screen.areas:
                if area.type == 'VIEW_3D':
                    if area.spaces.active:
                        area.spaces.active.region_3d.show_sync_view = True

        return {'FINISHED'}

    def invoke(self, context: bpy.types.Context, event: bpy.types.Event):
        return self.execute(context)


class SYNC_VIEW_OT_StopSync(bpy.types.Operator):
    """Disable sync on all visible viewports"""
    bl_idname = "syncview.stop_sync_all_visible"
    bl_label = "Stop Syncing Visible"

    @classmethod
    def poll(cls, context):
        return context.region_data

    def execute(self, context):
        for window in context.window_manager.windows:
            for area in window.screen.areas:
                if area.type == 'VIEW_3D':
                    if area.spaces.active:
                        area.spaces.active.region_3d.show_sync_view = False

        return {'FINISHED'}

    def invoke(self, context: bpy.types.Context, event: bpy.types.Event):
        return self.execute(context)


classes = [SYNC_VIEW_OT_EnableSync,
           SYNC_VIEW_OT_DisableSync,
           SYNC_VIEW_OT_SyncAllVisible,
           SYNC_VIEW_OT_StopSync,
           SYNC_VIEW_EVENTKEYMAP_OT_mouse_move
           ]


def register():
    register_classes(classes)

    keyconfigs_addon = bpy.context.window_manager.keyconfigs.addon
    # Keyamp bs: https://blender.stackexchange.com/questions/200811/is-there-a-reference-for-how-to-add-custom-keymaps-to-operators-in-an-addon
    if keyconfigs_addon:
        logger = logging.getLogger(__name__)
        logger.info("Registering syncview.report_active_area to 3D View keymap")

        keymap_sync_view = keyconfigs_addon.keymaps.new(name="3D View", space_type='VIEW_3D')
        keymap_sync_view.keymap_items.new(idname="syncview.report_active_area", type='MOUSEMOVE', value='ANY', any=True)


def unregister():
    driver_namespace = bpy.app.driver_namespace
    if 'sync_view' in driver_namespace and driver_namespace['sync_view'].has_handler():
        del bpy.app.driver_namespace['sync_view']

    # Reset attributes, it's not supposed to be True outside of this addon
    for window in bpy.context.window_manager.windows:
        for area in window.screen.areas:
            if area.type == 'VIEW_3D':
                area.spaces[0].region_3d.show_sync_view = False

    keyconfigs_addon = bpy.context.window_manager.keyconfigs.addon
    if keyconfigs_addon:
        keymap = keyconfigs_addon.keymaps.find("3D View", space_type='VIEW_3D')
        keymap_item = keymap.keymap_items.find_from_operator(idname="syncview.report_active_area")

        logger = logging.getLogger(__name__)
        logger.info("Removing syncview.report_active_area from 3D View keymap")

        keymap.keymap_items.remove(keymap_item)
        keyconfigs_addon.keymaps.remove(keymap)

    unregister_classes(classes)
