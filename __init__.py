import bpy
import time
bl_info = {
    "name": "Viewport Sync",
    "author": "Bowen Wu",
    "description": "Test",
    "blender": (2, 80, 3),
    "version": (4, 2, 0),
    "location": "",
    "warning": "",
    "category": ""
}

'''
import bpy
import gpu
from gpu_extras.presets import draw_texture_2d

WIDTH = 512
HEIGHT = 256

offscreen = gpu.types.GPUOffScreen(WIDTH, HEIGHT)


def draw():
    context = bpy.context
    scene = context.scene

    view_matrix = scene.camera.matrix_world.inverted()
    view3d = bpy.context.space_data
    
    
    view_matrix = view3d.region_3d.view_matrix
    perspective_matrix = view3d.region_3d.window_matrix.normalized()
    
    offscreen.draw_view3d(
        scene,
        context.view_layer,
        context.space_data,
        context.region,
        view_matrix,
        perspective_matrix,
        do_color_management=True)

    gpu.state.depth_mask_set(False)
    draw_texture_2d(offscreen.texture_color, (10, 10), WIDTH, HEIGHT)


bpy.types.SpaceView3D.draw_handler_add(draw, (), 'WINDOW', 'POST_PIXEL')
'''


def update_space(source_space, target_space):
    def update_attributes(source, target, attributes):
        for attribute in attributes:
            new_attribute = getattr(source, attribute, None)
            if new_attribute is not None:
                setattr(target, attribute, new_attribute)

    # Update space attributes, causes 2 additional redraws on target
    space_attributes = ['clip_end', 'clip_start', 'lens']
    update_attributes(source_space, target_space, space_attributes)
    # Update ViewRegion3D attributes
    # All modifiable attributes, causes 8 additional redraws on target
    view_region_3d_attributes = ['clip_planes', 'is_orthographic_side_view', 'is_perspective', 'lock_rotation', 'show_sync_view', 'use_box_clip', 'use_clip_planes',
                                 'view_camera_offset', 'view_camera_zoom', 'view_distance', 'view_location', 'view_perspective', 'view_rotation']
    # view_region_3d_attributes = ['view_matrix', 'view_camera_zoom',]
    update_attributes(source_space.region_3d, target_space.region_3d, view_region_3d_attributes)


def sync_views(context: bpy.types.Context, event, is_zoom=False):
    def is_out_of_area(area_xy, mouse_xy):
        return mouse_xy[0] < 0 or mouse_xy[0] > area_xy[0] or mouse_xy[1] < 0 or mouse_xy[1] > area_xy[0]
    time_start = time.time()
    context_area = context.area
    if context_area is None:
        print("context.area is none, returning with context" + str(context))
        return
    main_view_space = context.space_data

    # Handle zoom
    if is_zoom:
        print("Before", main_view_space.region_3d.view_distance)
        bpy.ops.view3d.zoom(delta=1 if event.type == 'WHEELUPMOUSE' else -1)
        main_view_space.region_3d.update()  # Force the value to be updated
        print("After", main_view_space.region_3d.view_distance)

    # Check if we're actually orbiting a viewport that's not from the original context and update the view space object
    if (is_out_of_area((context_area.width, context_area.height), (event.mouse_region_x, event.mouse_region_y))):
        print("Out of bounds!")
        for area in context.screen.areas:
            new_mouse_area_loc = (event.mouse_x - area.x,
                                  event.mouse_y - area.y)
            if area.ui_type == "VIEW_3D" and not is_out_of_area((area.width, area.height), new_mouse_area_loc):
                print("Main view region updated!")
                area.spaces[0].region_3d.view_distance = main_view_space.region_3d.view_distance
                main_view_space = area.spaces[0]
                main_view_space.region_3d.update()  # Force the value to be updated for zoom
                break
    # print(main_view_space.region_3d.view_distance, main_view_space.region_3d.view_location, main_view_space.region_3d.view_matrix)

    # Now update all 3d viewport spaces
    for area in context.screen.areas:
        # print(area.ui_type)
        if area.ui_type == "VIEW_3D":
            update_space(main_view_space, area.spaces[0])
    print("Viewport Sync Finished: %.4f sec" % (time.time() - time_start))


class SyncDraw:
    def __init__(self):
        self.add_handler()
        self.areas_to_sync = set()
        self.source_area = None
        self.redraw_counter = dict()

    # Handler order: PRE_VIEW, POST_VIEW, POST_PIXEL
    def add_handler(self):
        self.handlers = []
        self.handlers.append(bpy.types.SpaceView3D.draw_handler_add(
            self.sync_draw_callback, (), 'WINDOW', 'PRE_VIEW'))

    def has_handlers(self):
        return len(self.handlers) > 0

    def sync_draw_callback(self):
        context = bpy.context
        print("Callback on area:", context.area)

        this_area = context.area
        # print("Areas to sync", self.areas_to_sync)
        # print("Source area: ", self.source_area)
        # self.areas_to_sync = set()
        if this_area in self.redraw_counter:
            # if self.redraw_counter[this_area] > 0:
            #     self.redraw_counter[this_area] = self.redraw_counter[this_area] - 1
            #     print("early return, decrementing entry")
            #     return
            # else:
            self.redraw_counter.pop(this_area)
            print("Early return, removing entry")
            return

        if this_area in self.areas_to_sync:
            print("This area is marked for sync", this_area)
            update_space(self.source_area.spaces[0], this_area.spaces[0])
            self.areas_to_sync.remove(this_area)
            self.redraw_counter[this_area] = 0  # update_space causes 10 additional redraws, ignore those in here
            self.redraw_counter[self.source_area] = 0  # There will be one additional redraw for our source area
            # print("Area synced")
            return
        # elif this_area == self.source_area:
        #     print("Found self area, cleaing target area")
        #     self.source_area = None
        #     self.areas_to_sync = set()
        #     return
        # if self.areas_to_sync:
        #     print("Propagated drawcallsync on area", context.area)
        #     # self.remove_handler()
        #     return
        # print(" this area", source_area)
        # if self.source_area is not None:
        #     return
        source_area = context.area
        self.source_area = source_area
        print("New source area", source_area)
        for area in context.screen.areas:
            if area.type == "VIEW_3D" and area != source_area:
                # print("Other area:", area)
                self.areas_to_sync.add(area)
                area.tag_redraw()

        # print(self.areas_to_sync)
        # print("Update finished")

    def remove_handler(self):
        for handler in self.handlers:
            bpy.types.SpaceView3D.draw_handler_remove(handler, 'WINDOW')
        self.handlers = []


class SyncviewModal(bpy.types.Operator):
    """Tooltip"""
    bl_idname = "syncview.syncview_modal"
    bl_label = "Sync View Modal Operator"

    _syncing = False
    handler = None

    # def execute(self, context):

    #     sync_views(context)
    #     return {'FINISHED'}

    def invoke(self, context: bpy.types.Context, event: bpy.types.Event):
        if 'view_sync' not in bpy.app.driver_namespace:
            print("Adding handle")
            bpy.app.driver_namespace['view_sync'] = SyncDraw()
            return {'FINISHED'}

        if bpy.app.driver_namespace['view_sync'].has_handlers():
            print("Removing handle")
            bpy.app.driver_namespace['view_sync'].remove_handler()
            del bpy.app.driver_namespace['view_sync']

        return {'FINISHED'}

    # def modal(self, context, event):
    #     view3d = bpy.context.space_data

    #     print(view3d.render_border_min_x, view3d.render_border_max_x)

    #     for area in context.screen.areas:
    #         if area.type == "VIEW_3D":
    #             print(str(area) + " ", end="")
    #     print()
    #     if context.area is None:
    #         return {"FINISHED"}
    #     # TODO: Fix alt + middle mouse axis views
    #     if event.type == 'MIDDLEMOUSE' and event.value == 'PRESS' and not event.alt:
    #         self._syncing = True
    #         print("Syncing")
    #         return {'PASS_THROUGH'}
    #     elif event.type == 'MOUSEMOVE' and self._syncing:
    #         sync_views(context, event)
    #         self._syncing = False
    #         return {'PASS_THROUGH'}
    #     elif event.type in {'WHEELUPMOUSE', 'WHEELDOWNMOUSE'} and not (event.alt or event.ctrl or event.shift or event.oskey):
    #         # Since the zoom operator takes place after this, it will be delayed by one operation if we do not just handle zoom right here
    #         sync_views(context, event, True)
    #         return {'RUNNING_MODAL'}  # Consume the event and prevent regular zoom from occuring
    #     elif event.type == "RIGHTMOUSE":
    #         return {"FINISHED"}
    #     return {'PASS_THROUGH'}


def menu_func(self, context):
    self.layout.operator(SyncviewModal.bl_idname, text=SyncviewModal.bl_label)


# Register and add to the "object" menu (required to also use F3 search "Simple Object Operator" for quick access).
def register():
    bpy.utils.register_class(SyncviewModal)
    bpy.types.VIEW3D_MT_object.append(menu_func)


def unregister():
    bpy.utils.unregister_class(SyncviewModal)
    bpy.types.VIEW3D_MT_object.remove(menu_func)


if __name__ == "__main__":
    register()

    # test call
    bpy.ops.object.simple_operator()
