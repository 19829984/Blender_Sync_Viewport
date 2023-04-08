import bpy
from typing import List, Dict
import logging
import numpy as np

SPACE_ATTRIBUTES = ["clip_end", "clip_start", "lens"]
VIEW_REGION_3D_ATTRIBUTES = ["clip_planes", "is_orthographic_side_view", "is_perspective", "lock_rotation", "use_box_clip", "use_clip_planes",
                             "view_camera_offset", "view_camera_zoom", "view_distance", "view_location", "view_perspective", "view_rotation"]
VIEW_REGION_3D_ATTRIBUTES_TO_CHECK = ["is_orthographic_side_view", "is_perspective", "lock_rotation", "use_box_clip", "use_clip_planes",
                                      "view_camera_zoom"]
VIEW_REGION_3D_ARRAY_ATTRIBUTES_TO_CHECK = ["clip_planes", "view_camera_offset", "view_matrix"]


class SyncDrawHandler:
    """
    This class, when initialized, will add its sync_draw_callback() function to bpy.types.SpaceView3D's draw handler.

    For it to work properly, it must know what space and window the user is currently in, set through `active_space`
    and `active_window`. This is currently reported through the operator syncview.report_active_area, which is called
    on mouse move with any modifier key.

    Sync View relies on the show_sync_view attribute of bpy.types.RegionView3D. This attribute is currently only used
    for the quadview function as of Blender version 3.5; it has no effect outside of quadview. So we're making use
    of it to allow users to tag individual viewports to sync.
    """

    def __init__(self):
        self.active_space: bpy.types.Space = None

        self._handler: object = None
        self._active_window: bpy.types.Window = None
        self._logger: logging.Logger = logging.getLogger(__name__ + ".SyncDrawHandler")
        self._space_map: Dict[bpy.types.Space, (bpy.types.WorkSpace, bpy.types.Screen)] = dict()
        self._preferences: bpy.types.AddonPreferences = bpy.context.preferences.addons[__package__].preferences
        self._lock_sync: bool = False  # Rendering is done on a separate thread, this is to prevent race conditions
        self._last_viewport_attrs: list = []
        self.__add_handler()

    def set_active_window(self, new_window: bpy.types.Window) -> None:
        """
        Update the stored active window. If the new window is different than the old one,
        then rebuild the internal space map dictionary

        Args:
            new_window (bpy.types.Window): new window object to be stored
        """
        self._lock_sync = True
        if self._active_window != new_window:
            self.__rebuild_space_map(new_window)
        self._lock_sync = False
        self._active_window = new_window

    active_window = property(fset=set_active_window)

    def __rebuild_space_map_window(self, window: bpy.types.Window) -> None:
        """
        Rebuild the space map for each viewport in the window tagged for sync

        Args:
            window (bpy.types.Window): window to have viewports synced in
        """
        if "sync_view.do_not_sync" not in window.screen:
            self._space_map = {
                area.spaces.active: (window.workspace, window.screen)
                for area in window.screen.areas
                if area.type == 'VIEW_3D' and area.spaces.active.region_3d.show_sync_view
            }

    def __rebuild_space_map(self, window: bpy.types.Window) -> None:
        """
        Clear and rebuild the space map depending on the current sync mode.
        Uses window argument when in window sync mode.

        This populates _space_map with key value pairs that maps a space to
        a tuple containing its workspace and screen{space : (workspace, screen)}

        Args:
            window (bpy.types.Window): window to have viewports synced in
        """
        sync_mode = self._preferences.sync_modes[self._preferences.sync_mode]
        match sync_mode:
            # Window Sync
            case 0:
                self.__rebuild_space_map_window(window)
            # Workspace sync
            case 1:
                # Rebuild the space map for each viewport in the current workspace tagged for sync
                new_spacemap = dict()

                # Use the workspace of an open window instead of bpy.context.workspace
                # because for some reason those two can be different
                workspace_window_any = bpy.context.window_manager.windows[0]
                workspace, screens = workspace_window_any.workspace, workspace_window_any.workspace.screens

                valid_screens = {
                    window.screen for window in bpy.context.window_manager.windows
                    if "sync_view.do_not_sync" not in window.screen
                }
                for screen in screens:
                    if screen in valid_screens and hasattr(screen, "areas"):
                        for area in screen.areas:
                            active_space = area.spaces.active
                            if area.type == 'VIEW_3D' and active_space and active_space.region_3d.show_sync_view:
                                new_spacemap[active_space] = (workspace, screen)
                    else:  # These should be screens that are closed in the current workspace
                        screen["sync_view.do_not_sync"] = True
                self._space_map = new_spacemap
            # All Sync
            case 2:
                # Rebuild the space map for all viewport in the blend file tagged for sync
                new_spacemap = dict()

                # Use the workspace of an open window instead of bpy.context.workspace
                # because for some reason those two can be different
                workspace_window_any = bpy.context.window_manager.windows[0]
                workspace_screens = set(workspace_window_any.workspace.screens)
                valid_workspace_screens = {
                    window.screen for window in bpy.context.window_manager.windows
                    if "sync_view.do_not_sync" not in window.screen
                }
                # We cannot be certain if a screen outside of the current workspace is closed and should not be synced
                other_workspace_screens = {
                    screen for screen in bpy.context.blend_data.screens
                    if ("sync_view.do_not_sync" not in screen and screen not in workspace_screens)
                }

                screens = valid_workspace_screens.union(other_workspace_screens)

                for workspace in bpy.context.blend_data.workspaces:
                    for screen in workspace.screens:
                        if screen in screens and hasattr(screen, "areas"):
                            for area in screen.areas:
                                active_space = area.spaces.active
                                if area.type == 'VIEW_3D' and active_space and active_space.region_3d.show_sync_view:
                                    new_spacemap[active_space] = (workspace_window_any.workspace, screen)
                        else:  # These should be screens that are closed in the current workspace
                            screen["sync_view.do_not_sync"] = True
                self._space_map = new_spacemap
            case _:
                self.__rebuild_space_map_window(window)

    # Handler order: PRE_VIEW, POST_VIEW, POST_PIXEL

    def __add_handler(self) -> None:
        """
        Add a draw handler to bpy.types.SpapceView3D from this class
        """
        self._handler = bpy.types.SpaceView3D.draw_handler_add(self.sync_draw_callback, (), 'WINDOW', 'PRE_VIEW')
        self._logger.info("Adding a sync view draw handler")

    def __has_viewport_changed(self, space: bpy.types.Space) -> bool:
        """
        Returns if the given space has a different view than the stored view data in _last_viewport_attrs

        Args:
            space (bpy.types.Space): space to check the stored view data against

        Returns:
            bool: If the given space has a different view than the stored view data in _last_viewport_attrs
        """
        if not self._last_viewport_attrs:
            return False
        view_port_attrs_index = 0
        for attr in SPACE_ATTRIBUTES:
            if getattr(space, attr, None) != self._last_viewport_attrs[view_port_attrs_index]:
                return True
            view_port_attrs_index += 1
        for attr in VIEW_REGION_3D_ATTRIBUTES_TO_CHECK:
            if getattr(space.region_3d, attr, None) != self._last_viewport_attrs[view_port_attrs_index]:
                return True
            view_port_attrs_index += 1
        for attr in VIEW_REGION_3D_ARRAY_ATTRIBUTES_TO_CHECK:
            if not np.allclose(np.array(getattr(space.region_3d, attr, None)), self._last_viewport_attrs[view_port_attrs_index]):
                return True
            view_port_attrs_index += 1
        return False

    # Storing these attributes are inepensive, seems to be sub nanoseconds on a Ryzen 5900X
    def __store_viewport_attrs(self, space: bpy.types.Space) -> None:
        """
        Stores the space's view data in _last_viewport_attrs in the order of attributes in
        SPACE_ATTRIBUTES, VIEW_REGION_3D_ATTRIBUTES_TO_CHECK, and
        VIEW_REGION_3D_ARRAY_ATTRIBUTES_TO_CHECK

        Args:
            space (bpy.types.Space): space to have its view attributes stored
        """
        self._last_viewport_attrs = [getattr(space, attr, None) for attr in SPACE_ATTRIBUTES]
        self._last_viewport_attrs += [getattr(space.region_3d, attr, None) for attr in VIEW_REGION_3D_ATTRIBUTES_TO_CHECK]
        self._last_viewport_attrs += [np.array(getattr(space.region_3d, attr, None)) for attr in VIEW_REGION_3D_ARRAY_ATTRIBUTES_TO_CHECK]

    def __update_space(self, target_space: bpy.types.Space) -> None:
        """
        Updates target_space so that it has the same view as the stored active space

        Args:
            target_space (bpy.types.Space): space to update the view to
        """
        def copy_attributes(source: object, target: object, attributes: List[str]) -> None:
            """
            Copy all attribtutes, given as list of strings, from source object to target object

            Args:
                source (object): source object to copy attributes from
                target (object): target object to copy attributes to
                attributes (List[str]): list of attribute names
            """
            for attribute in attributes:
                new_attribute = getattr(source, attribute, None)
                if new_attribute is not None:
                    setattr(target, attribute, new_attribute)

        # Update space attributes
        copy_attributes(self.active_space, target_space, SPACE_ATTRIBUTES)

        # Update ViewRegion3D attributes
        copy_attributes(self.active_space.region_3d, target_space.region_3d, VIEW_REGION_3D_ATTRIBUTES)

    def build_map(self) -> None:
        """
        Build the spacemap with the stored active window
        """
        self._lock_sync = True
        self.__rebuild_space_map(self._active_window)
        self._lock_sync = False

    def remove_handler(self) -> None:
        """
        Remove the draw handler from this class from bpy.types.SpapceView3D
        """
        self._logger.info("Removing sync view draw handler")
        bpy.types.SpaceView3D.draw_handler_remove(self._handler, 'WINDOW')
        self._handler = None

    def has_handler(self) -> bool:
        return self._handler is not None

    def sync_draw_callback(self) -> None:
        """
        Will sync all viewports tagged for sync to the same view as the viewport this
        callback function is called from, if the viewport is tagged for sync.

        Will not sync if any of the following conditions are fulfilled, evaluated in order:
        - The viewport is not tagged for sync, or there's not recorded active space
        - The current space is in quad view mode
        - _lock_sync is true, this is to prevent sync while space_map is being rebuilt
        - Addon preferences has pause_sync enabled
        - Addon preferences has sync_playback disabled and the viewport is playing an animation
        - Addon preferences has sync_camera_view disabled and the viewport is in camera view
        - self.__has_viewport_changed(bpy.context.space_data) returns false
        """
        this_space = bpy.context.space_data

        if not bpy.context.region_data.show_sync_view or not self.active_space:
            self._space_map.pop(this_space, None)
            return

        # Disable sync if in quadview to prevent issues
        if len(this_space.region_quadviews) > 1:
            if this_space.region_3d.show_sync_view:
                this_space.region_3d.show_sync_view = False
            return

        if self._lock_sync:
            return

        if self._preferences.pause_sync:
            return

        if bpy.context.screen.is_animation_playing and not self._preferences.sync_playback:
            return

        if not self._preferences.sync_camera_view and bpy.context.space_data.region_3d.view_perspective == 'CAMERA':
            return

        # Use the workspace of an open window instead of bpy.context.workspace
        # because for some reason those two can be different
        self._space_map[this_space] = (bpy.context.window_manager.windows[0].workspace, bpy.context.screen)

        # Sync other viewports
        if this_space == self.active_space:
            if not self._last_viewport_attrs:
                # Initialize self._last_viewport_attrs
                self.__store_viewport_attrs(this_space)
            elif (self.__has_viewport_changed(this_space)):
                self.__store_viewport_attrs(this_space)

                sync_mode = self._preferences.sync_modes[self._preferences.sync_mode]

                spaces_to_sync = set()
                spaces = self._space_map.keys()
                # Cleanup invalid spaces
                # Use .region_3d to check if viewport is still valid
                match sync_mode:
                    case 0:  # Window Sync
                        spaces_to_sync = {
                            space for space in spaces
                            if (space.region_3d and self._space_map[space][1] == self._space_map[self.active_space][1])
                        }
                    case 1:  # Workspace Sync
                        spaces_to_sync = {
                            space for space in spaces
                            if (space.region_3d and self._space_map[space][0] == self._space_map[self.active_space][0])
                        }
                    case 2:  # All Sync
                        spaces_to_sync = {
                            space for space in spaces
                            if space.region_3d
                        }
                    case _:  # Default to Window Sync
                        spaces_to_sync = {
                            space for space in spaces
                            if (space.region_3d and self._space_map[space][1] == self._space_map[self.active_space][1])
                        }
                spaces_to_sync.remove(this_space)
                for space in spaces_to_sync:
                    if space.region_3d.show_sync_view:
                        self.__update_space(space)
