import bpy
from typing import List, Dict
import logging
# import time
import numpy as np

SPACE_ATTRIBUTES = ["clip_end", "clip_start", "lens"]
VIEW_REGION_3D_ATTRIBUTES = ["clip_planes", "is_orthographic_side_view", "is_perspective", "lock_rotation", "use_box_clip", "use_clip_planes",
                             "view_camera_offset", "view_camera_zoom", "view_distance", "view_location", "view_perspective", "view_rotation"]
VIEW_REGION_3D_ATTRIBUTES_TO_CHECK = ["is_orthographic_side_view", "is_perspective", "lock_rotation", "use_box_clip", "use_clip_planes",
                                      "view_camera_zoom"]
VIEW_REGION_3D_ARRAY_ATTRIBUTES_TO_CHECK = ["clip_planes", "view_camera_offset", "view_matrix"]


class SyncDrawHandler:
    def __init__(self):
        self.active_space: bpy.types.Space = None

        self._handlers: List[object] = []
        self._active_window: bpy.types.Window = None
        self._logger: logging.Logger = logging.getLogger(__name__ + ".SyncDrawHandler")
        self._space_map: Dict[bpy.types.Space, (bpy.types.WorkSpace, bpy.types.Screen)] = dict()
        self._preferences: bpy.types.AddonPreferences = bpy.context.preferences.addons[__package__].preferences
        self._lock_sync: bool = False  # Rendering is done on a separate thread, this is to prevent race conditions
        self._last_viewport_attrs: list = []
        self.__add_handlers()

    def set_active_window(self, new_window: bpy.types.Window) -> None:
        '''
        Update the stored active window. If the new window is different than the old one,
        then rebuild the internal space map dictionary
        '''
        self._lock_sync = True
        if self._active_window != new_window:
            self.__rebuild_space_map(new_window)
        self._lock_sync = False
        self._active_window = new_window

    active_window = property(fset=set_active_window)

    def __rebuild_space_map_window(self, new_window: bpy.types.Window) -> None:
        '''Rebuild the space map for each viewport in the current window tagged for sync'''
        self._space_map = dict()
        if "sync_view.do_not_sync" not in new_window.screen:
            for area in new_window.screen.areas:
                if area.type == 'VIEW_3D' and area.spaces.active.region_3d.show_sync_view:
                    self._space_map[area.spaces.active] = (new_window.workspace, new_window.screen)

    def __rebuild_space_map(self, new_window: bpy.types.Window) -> None:
        '''
        Clear and rebuild the space map depending on the current sync mode

        This populates _space_map with key value pairs that maps a space to 
        a tuple containing its workspace and screen{space : (workspace, screen)}
        '''
        sync_mode = self._preferences.sync_modes[self._preferences.sync_mode]
        match sync_mode:
            case 0:  # Window Sync
                self.__rebuild_space_map_window(new_window)
            case 1:  # Workspace sync
                # Rebuild the space map for each viewport in the current workspace tagged for sync
                self._space_map = dict()

                # Use the workspace of an open window instead of bpy.context.workspace
                # because for some reason those two can be different
                workspace_window_any = bpy.context.window_manager.windows[0]
                workspace, screens = workspace_window_any.workspace, workspace_window_any.workspace.screens

                valid_screens = {
                    window.screen for window in bpy.context.window_manager.windows if "sync_view.do_not_sync" not in window.screen}
                for screen in screens:
                    if screen in valid_screens and hasattr(screen, "areas"):
                        for area in screen.areas:
                            active_space = area.spaces.active
                            if area.type == 'VIEW_3D' and active_space and active_space.region_3d.show_sync_view:
                                self._space_map[active_space] = (workspace, screen)
                    else:  # These should be screens that are closed in the current workspace
                        screen["sync_view.do_not_sync"] = True
            case 2:  # All Sync
                # Rebuild the space map for all viewport in the blend file tagged for sync
                self._space_map = dict()

                # Use the workspace of an open window instead of bpy.context.workspace
                # because for some reason those two can be different
                workspace_window_any = bpy.context.window_manager.windows[0]
                workspace_screens = set(workspace_window_any.workspace.screens)
                valid_workspace_screens = {
                    window.screen for window in bpy.context.window_manager.windows if "sync_view.do_not_sync" not in window.screen}
                # We cannot be certain if a screen outside of the current workspace is closed and should not be synced
                other_workspace_screens = {
                    screen for screen in bpy.context.blend_data.screens
                    if ("sync_view.do_not_sync" not in screen and screen not in workspace_screens)}

                screens = valid_workspace_screens.union(other_workspace_screens)

                for workspace in bpy.context.blend_data.workspaces:
                    for screen in workspace.screens:
                        if screen in screens and hasattr(screen, "areas"):
                            for area in screen.areas:
                                active_space = area.spaces.active
                                if area.type == 'VIEW_3D' and active_space and active_space.region_3d.show_sync_view:
                                    self._space_map[active_space] = (workspace_window_any.workspace, screen)
                        else:  # These should be screens that are closed in the current workspace
                            screen["sync_view.do_not_sync"] = True
            case _:
                self.__rebuild_space_map_window(new_window)

    # Handler order: PRE_VIEW, POST_VIEW, POST_PIXEL

    def __add_handlers(self) -> None:
        self._handlers.append(bpy.types.SpaceView3D.draw_handler_add(
            self.sync_draw_callback, (), 'WINDOW', 'PRE_VIEW'))
        self._logger.info("Adding a sync view draw handler")
        self._logger.info("Handlers: " + str(self._handlers))

    def __has_viewport_changed(self, space: bpy.types.Space) -> bool:
        # time_start = time.time()
        if not self._last_viewport_attrs:
            return False
        view_port_attrs_index = 0
        for attr in SPACE_ATTRIBUTES:
            if getattr(space, attr, None) != self._last_viewport_attrs[view_port_attrs_index]:
                # self._logger.info("0 Checking viewport change took " + str(time.time() - time_start))
                return True
            view_port_attrs_index += 1
        for attr in VIEW_REGION_3D_ATTRIBUTES_TO_CHECK:
            if getattr(space.region_3d, attr, None) != self._last_viewport_attrs[view_port_attrs_index]:
                # self._logger.info("1 Checking viewport change took " + str(time.time() - time_start))
                return True
            view_port_attrs_index += 1
        for attr in VIEW_REGION_3D_ARRAY_ATTRIBUTES_TO_CHECK:
            if not np.allclose(np.array(getattr(space.region_3d, attr, None)), self._last_viewport_attrs[view_port_attrs_index]):
                # self._logger.info("2 Checking viewport change took " + str(time.time() - time_start))
                return True
            view_port_attrs_index += 1
        # self._logger.info("3 Checking viewport change took " + str(time.time() - time_start))
        return False

    # Storing these attributes are inepensive, seems to be sub nanoseconds on a Ryzen 5900X
    def __store_viewport_attrs(self, space: bpy.types.Space) -> None:
        # time_start = time.time()
        self._last_viewport_attrs = []
        for attr in SPACE_ATTRIBUTES:
            self._last_viewport_attrs.append(getattr(space, attr, None))
        for attr in VIEW_REGION_3D_ATTRIBUTES_TO_CHECK:
            self._last_viewport_attrs.append(getattr(space.region_3d, attr, None))
        for attr in VIEW_REGION_3D_ARRAY_ATTRIBUTES_TO_CHECK:
            self._last_viewport_attrs.append(np.array(getattr(space.region_3d, attr, None)))
        # self._logger.info("Time to store viewprt attrs " + str(time.time() - time_start))

    def __update_space(self, target_space: bpy.types.Space) -> None:
        def copy_attributes(source: object, target: object, attributes: List[str]) -> None:
            '''Copy all attribtutes, given as list of strings, from source object to target object'''
            for attribute in attributes:
                new_attribute = getattr(source, attribute, None)
                if new_attribute is not None:
                    setattr(target, attribute, new_attribute)

        # Update space attributes
        copy_attributes(self.active_space, target_space, SPACE_ATTRIBUTES)

        # Update ViewRegion3D attributes
        copy_attributes(self.active_space.region_3d, target_space.region_3d, VIEW_REGION_3D_ATTRIBUTES)

    def build_map(self) -> None:
        self._lock_sync = True
        self.__rebuild_space_map(self._active_window)
        self._lock_sync = False

    def remove_handlers(self) -> None:
        self._logger.info("Removing sync view draw handlers")
        for handler in self._handlers:
            bpy.types.SpaceView3D.draw_handler_remove(handler, 'WINDOW')
        self._handlers = []

    def has_handlers(self) -> bool:
        return len(self._handlers) > 0

    def sync_draw_callback(self) -> None:
        this_space = bpy.context.space_data

        # Disable sync if in quadview to prevent issues
        if len(this_space.region_quadviews) > 1:
            if this_space.region_3d.show_sync_view:
                this_space.region_3d.show_sync_view = False
            return

        if self._preferences.pause_sync:
            return

        if bpy.context.screen.is_animation_playing and not self._preferences.sync_playback:
            return

        if not self._preferences.sync_camera_view and bpy.context.space_data.region_3d.view_perspective == 'CAMERA':
            return

        if self._lock_sync:
            return

        if not bpy.context.region_data.show_sync_view or not self.active_space:
            self._space_map.pop(this_space, None)
            return

        # Use the workspace of an open window instead of bpy.context.workspace
        # because for some reason those two can be different
        self._space_map[this_space] = (bpy.context.window_manager.windows[0].workspace, bpy.context.screen)

        # Sync other viewports
        if this_space == self.active_space:
            if not self._last_viewport_attrs:
                self.__store_viewport_attrs(this_space)
            elif (self.__has_viewport_changed(this_space)):
                self.__store_viewport_attrs(this_space)

                # Cleanup invalid spaces
                sync_mode = self._preferences.sync_modes[self._preferences.sync_mode]
                # Use .region_3d to check if viewport is still valid
                spaces_to_sync = set()
                spaces = self._space_map.keys()
                match sync_mode:
                    case 0:  # Window Sync
                        spaces_to_sync = {
                            space for space in spaces
                            if (space.region_3d and self._space_map[space][1] == self._space_map[self.active_space][1]
                                )
                        }
                    case 1:  # Workspace Sync
                        spaces_to_sync = {
                            space for space in spaces
                            if (space.region_3d and self._space_map[space][0] == self._space_map[self.active_space][0]
                                )
                        }
                    case 2:  # All Sync
                        spaces_to_sync = {
                            space for space in spaces
                            if space.region_3d
                        }
                    case _:  # Default to Window Sync
                        spaces_to_sync = {
                            space for space in spaces
                            if (space.region_3d and self._space_map[space][1] == self._space_map[self.active_space][1]
                                )
                        }
                spaces_to_sync.remove(this_space)
                for space in spaces_to_sync:
                    if space.region_3d.show_sync_view:
                        self.__update_space(space)
