import bpy
import logging


def register():
    driver_namespace = bpy.app.driver_namespace
    owner = driver_namespace

    key = (bpy.types.RegionView3D, "show_sync_view")

    def sync_view_callback(*args):
        if 'view_sync' not in bpy.app.driver_namespace:
            logger = logging.getLogger(__name__ + ".MsgBusSyncViewCallback")
            logger.info("Sync enabled for a viewport, enabling sync draw handler")
            bpy.ops.syncview.syncview_enable_sync()

    bpy.msgbus.subscribe_rna(
        key=key,
        owner=owner,
        args=(),
        notify=sync_view_callback,
    )


def unregister():
    driver_namespace = bpy.app.driver_namespace
    bpy.msgbus.clear_by_owner(driver_namespace)
