import bpy
import logging


def register():
    driver_namespace = bpy.app.driver_namespace
    owner = driver_namespace

    def sync_view_callback(*args):
        if 'sync_view' not in bpy.app.driver_namespace:
            logger = logging.getLogger(__name__ + ".MsgBusSyncViewCallback")
            logger.info("Enabling sync draw handler")
            bpy.ops.syncview.syncview_enable_sync()
        else:
            bpy.app.driver_namespace['sync_view'].build_map()

    # Callback for when a viewport's show_sync_view RNA property changes
    key = (bpy.types.RegionView3D, "show_sync_view")
    bpy.msgbus.subscribe_rna(
        key=key,
        owner=owner,
        args=(),
        notify=sync_view_callback,
    )

    # Callback for when we switch viewport types
    key = (bpy.types.Window, "workspace")
    bpy.msgbus.subscribe_rna(
        key=key,
        owner=owner,
        args=(),
        notify=sync_view_callback,
    )


def unregister():
    driver_namespace = bpy.app.driver_namespace
    bpy.msgbus.clear_by_owner(driver_namespace)
