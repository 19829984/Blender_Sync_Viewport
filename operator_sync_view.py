import bpy
from .sync_handler import SyncDrawHandler
from .utils.registration import *


class SyncView_OT_Enable_Sync_Modal(bpy.types.Operator):
    """"""
    bl_idname = "syncview.syncview_enable_syncmodal"
    bl_label = "Enable Sync View Modal Operator"

    def modal(self, context, event):
        if 'view_sync' in bpy.app.driver_namespace:
            bpy.app.driver_namespace['view_sync'].update_mouse_pos((event.mouse_x, event.mouse_y))
            return {"PASS_THROUGH"}
        else:
            print("Ending modal")
            return {'FINISHED'}

    def execute(self, context):
        if 'view_sync' not in bpy.app.driver_namespace:
            context.window_manager.modal_handler_add(self)
            bpy.app.driver_namespace['view_sync'] = SyncDrawHandler()
        return {'RUNNING_MODAL'}

    def invoke(self, context: bpy.types.Context, event: bpy.types.Event):
        return self.execute(context)


class SyncView_OT_Disable_Sync_Modal(bpy.types.Operator):
    """"""
    bl_idname = "syncview.syncview_disable_syncmodal"
    bl_label = "Disable Sync View Modal Operator"

    def execute(self, context):
        driver_namespace = bpy.app.driver_namespace
        if 'view_sync' in driver_namespace and driver_namespace['view_sync'].has_handlers():
            driver_namespace['view_sync'].remove_handler()
            del bpy.app.driver_namespace['view_sync']

        return {'FINISHED'}

    def invoke(self, context: bpy.types.Context, event: bpy.types.Event):
        return self.execute(context)


classes = [SyncView_OT_Enable_Sync_Modal, SyncView_OT_Disable_Sync_Modal]


def register():
    print("Registering sync view")
    register_classes(classes)


def unregister():
    unregister_classes(classes)
