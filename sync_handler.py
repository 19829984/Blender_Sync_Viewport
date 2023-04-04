import bpy
from typing import Set
import logging


def update_space(source_space, target_space):
    def update_attributes(source, target, attributes):
        for attribute in attributes:
            new_attribute = getattr(source, attribute, None)
            if new_attribute is not None:
                setattr(target, attribute, new_attribute)

    # Update space attributes
    space_attributes = ['clip_end', 'clip_start', 'lens']
    update_attributes(source_space, target_space, space_attributes)

    # Update ViewRegion3D attributes
    # All modifiable attributes
    view_region_3d_attributes = ['clip_planes', 'is_orthographic_side_view', 'is_perspective', 'lock_rotation', 'use_box_clip', 'use_clip_planes',
                                 'view_camera_offset', 'view_camera_zoom', 'view_distance', 'view_location', 'view_perspective', 'view_rotation']
    update_attributes(source_space.region_3d, target_space.region_3d, view_region_3d_attributes)


class SyncDrawHandler:
    def __init__(self):
        self._handlers = []
        self.active_area = None
        self._active_window = None
        self._skip_sync: bool = False
        self._areas: Set[bpy.types.Area] = set()
        self._logger = logging.getLogger(__name__ + ".SyncDrawHandler")
        self.__add_handlers()

    def __del__(self):
        self.remove_handlers()

    def set_active_window(self, new_window: bpy.types.Window):
        if self._active_window != new_window:
            self._areas = set()
            for area in new_window.screen.areas:
                if area.type == "VIEW_3D" and area.spaces[0].region_3d.show_sync_view:
                    self._areas.add(area)
        self._active_window = new_window

    active_window = property(fset=set_active_window)

    # Handler order: PRE_VIEW, POST_VIEW, POST_PIXEL

    def __add_handlers(self):
        self._handlers.append(bpy.types.SpaceView3D.draw_handler_add(
            self.sync_draw_callback, (), 'WINDOW', 'PRE_VIEW'))
        self._logger.info("Adding a draw handler")
        self._logger.info("Handlers: " + str(self._handlers))

    def remove_handlers(self):
        self._logger.info("Removing view sync draw handlers")
        for handler in self._handlers:
            bpy.types.SpaceView3D.draw_handler_remove(handler, 'WINDOW')
        self._handlers = []

    def has_handlers(self):
        return len(self._handlers) > 0

    def sync_draw_callback(self):
        if not bpy.context.region_data.show_sync_view or not self.active_area or not self._active_window:
            self._areas.discard(bpy.context.area)
            return

        self._areas.add(bpy.context.area)

        # Cleanup invalid areas
        invalid_areas = set()
        for area in self._areas:
            if not area.path_resolve("height") or area not in self._active_window.screen.areas.values():
                invalid_areas.add(area)
        for area in invalid_areas:
            self._areas.remove(area)

        # Sync other viewports
        if bpy.context.area == self.active_area:
            # For some reason updating another viewport causes this viewport to have an additional redraw, so we skip
            if self._skip_sync:
                self._skip_sync = False
                return
            self._skip_sync = True

            # TODO: conditionally loop over all windows and screens to sync between windows.
            for area in self._areas:
                if area != bpy.context.area and area.spaces[0].region_3d.show_sync_view:
                    update_space(bpy.context.area.spaces[0], area.spaces[0])
        return
