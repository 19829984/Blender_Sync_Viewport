import bpy
from .sync_handler import SyncDrawHandler
from .utils.registration import *


class EVENTKEYMAP_OT_mouse_move(bpy.types.Operator):
    """
    This operator reports mouse position to our draw handler, is meant to be called through a keymap on mouse move
    Adopted from https://blender.stackexchange.com/questions/267285/alternative-to-modal-operators-blocked-autosave
    """
    bl_idname = "syncview.report_mouse_pos"
    bl_label = "Report mouse position"

    def invoke(self, context: bpy.types.Context, event: bpy.types.Event):
        if (context is None) or (context.area is None):
            return {'PASS_THROUGH'}

        if 'view_sync' in bpy.app.driver_namespace:
            view_sync = bpy.app.driver_namespace['view_sync']
            view_sync.active_area = context.area

        return {'PASS_THROUGH'}


class SyncView_OT_Enable_Sync(bpy.types.Operator):
    """"""
    bl_idname = "syncview.syncview_enable_sync"
    bl_label = "Enable Sync View Operator"

    def execute(self, context):
        driver_namespace = bpy.app.driver_namespace
        if 'view_sync' not in driver_namespace:
            driver_namespace['view_sync'] = SyncDrawHandler()
        return {'FINISHED'}

    def invoke(self, context: bpy.types.Context, event: bpy.types.Event):
        return self.execute(context)


class SyncView_OT_Disable_Sync(bpy.types.Operator):
    """"""
    bl_idname = "syncview.syncview_disable_sync"
    bl_label = "Disable Sync View Operator"

    def execute(self, context):
        driver_namespace = bpy.app.driver_namespace
        if 'view_sync' in driver_namespace and driver_namespace['view_sync'].has_handlers():
            driver_namespace['view_sync'].remove_handler()
            del bpy.app.driver_namespace['view_sync']

        return {'FINISHED'}

    def invoke(self, context: bpy.types.Context, event: bpy.types.Event):
        return self.execute(context)


classes = [SyncView_OT_Enable_Sync, SyncView_OT_Disable_Sync, EVENTKEYMAP_OT_mouse_move]


def register():
    register_classes(classes)

    keyconfigs_addon = bpy.context.window_manager.keyconfigs.addon
    # Keyamp bs: https://blender.stackexchange.com/questions/200811/is-there-a-reference-for-how-to-add-custom-keymaps-to-operators-in-an-addon
    if keyconfigs_addon:
        keymap_sync_view = keyconfigs_addon.keymaps.new(name="3D View", space_type='VIEW_3D')
        keymap_sync_view.keymap_items.new(idname="syncview.report_mouse_pos", type='MOUSEMOVE', value='ANY')


def unregister():
    keyconfigs_addon = bpy.context.window_manager.keyconfigs.addon
    if keyconfigs_addon:
        keymap = keyconfigs_addon.keymaps.find("3D View", space_type="VIEW_3D")
        keymap_item = keymap.keymap_items.find_from_operator(idname="syncview.report_mouse_pos")

        keymap.keymap_items.remove(keymap_item)
        keyconfigs_addon.keymaps.remove(keymap)

    unregister_classes(classes)
