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
        self.active_space: bpy.types.Space = None

        self._handlers = []
        self._active_window = None
        self._skip_sync: bool = False
        self._spaces: Set[bpy.types.Space] = set()
        self._logger = logging.getLogger(__name__ + ".SyncDrawHandler")
        self._space_map = dict()
        self._preferences = bpy.context.preferences.addons[__package__].preferences
        self._lock_sync = False  # Rendering is done on a separate thread, this is to prevent race conditions
        self.__add_handlers()

    def set_active_window(self, new_window: bpy.types.Window):
        self._lock_sync = True
        if self._active_window != new_window:
            self.__rebuild_space_map(new_window)
        self._lock_sync = False
        self._active_window = new_window

    active_window = property(fset=set_active_window)

    def __rebuild_window(self, new_window: bpy.types.Window):
        self._spaces = set()
        self._space_map = dict()
        if "sync_view.do_not_sync" not in new_window.screen:
            for area in new_window.screen.areas:
                if area.type == "VIEW_3D" and area.spaces.active.region_3d.show_sync_view:
                    self._spaces.add(area.spaces.active)
                    self._space_map[area.spaces.active] = (new_window.workspace, new_window.screen)

    def __rebuild_space_map(self, new_window):
        sync_mode = self._preferences.sync_modes[self._preferences.sync_mode]
        match sync_mode:
            case 0:  # Window Sync
                self.__rebuild_window(new_window)
            case 1:  # Workspace sync
                self._spaces = set()
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
                            if area.type == "VIEW_3D" and active_space and active_space.region_3d.show_sync_view:
                                self._spaces.add(active_space)
                                self._space_map[active_space] = (workspace, screen)
                    else:  # These should be screens that are closed in the current workspace
                        screen["sync_view.do_not_sync"] = True
            case 2:  # All Sync
                self._spaces = set()
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
                                if area.type == "VIEW_3D" and active_space and active_space.region_3d.show_sync_view:
                                    self._spaces.add(active_space)
                                    self._space_map[active_space] = (workspace_window_any.workspace, screen)
                        else:  # These should be screens that are closed in the current workspace
                            screen["sync_view.do_not_sync"] = True
            case _:
                self.__rebuild_window(new_window)

    def build_space_map(self):
        self._lock_sync = True
        self.__rebuild_space_map(self._active_window)
        self._lock_sync = False

    # Handler order: PRE_VIEW, POST_VIEW, POST_PIXEL

    def __add_handlers(self):
        self._handlers.append(bpy.types.SpaceView3D.draw_handler_add(
            self.sync_draw_callback, (), 'WINDOW', 'PRE_VIEW'))
        self._logger.info("Adding a sync view draw handler")
        self._logger.info("Handlers: " + str(self._handlers))

    def remove_handlers(self):
        self._logger.info("Removing sync view draw handlers")
        for handler in self._handlers:
            bpy.types.SpaceView3D.draw_handler_remove(handler, 'WINDOW')
        self._handlers = []

    def has_handlers(self):
        return len(self._handlers) > 0

    # TODO: Time our sync callback comapred to areas solution
    def sync_draw_callback(self):
        if self._lock_sync:
            return

        this_space = bpy.context.space_data
        if not bpy.context.region_data.show_sync_view or not self.active_space:
            self._spaces.discard(this_space)
            return

        # Use the workspace of an open window instead of bpy.context.workspace
        # because for some reason those two can be different
        self._space_map[this_space] = (bpy.context.window_manager.windows[0].workspace, bpy.context.screen)
        self._spaces.add(this_space)

        # Sync other viewports
        if this_space == self.active_space:
            # For some reason updating another viewport causes this viewport to have an additional redraw, so we skip
            if self._skip_sync:
                self._skip_sync = False
                return
            self._skip_sync = True

            # Cleanup invalid spaces
            sync_mode = self._preferences.sync_modes[self._preferences.sync_mode]
            # Use .region_3d to check if viewport is still valid
            match sync_mode:
                case 0:  # Window Sync
                    self._spaces = {
                        space for space in self._spaces
                        if (space.region_3d and
                            self._space_map[space][1] == self._space_map[self.active_space][1]
                            )
                    }
                case 1:  # Workspace Sync
                    self._spaces = {
                        space for space in self._spaces
                        if (space.region_3d and
                            self._space_map[space][0] == self._space_map[self.active_space][0]
                            )
                    }
                case 2:  # All Sync
                    self._spaces = {
                        space for space in self._spaces
                        if space.region_3d
                    }
                case _:  # Default to Window Sync
                    self._spaces = {
                        space for space in self._spaces
                        if (space.region_3d and
                            self._space_map[space][1] == self._space_map[self.active_space][1]
                            )
                    }
            self._spaces.remove(this_space)
            for space in self._spaces:
                if space.region_3d.show_sync_view:
                    update_space(this_space, space)
        return
