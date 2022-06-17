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


def sync_views(context, event, is_zoom=False):
    def is_out_of_area(area_xy, mouse_xy):
        return mouse_xy[0] < 0 or mouse_xy[0] > area_xy[0] or mouse_xy[1] < 0 or mouse_xy[1] > area_xy[0]
    time_start = time.time()
    context_area = context.area
    main_view_space = context.space_data
    
    def update_space(source_space, target_space):
        def update_attributes(source, target, attributes):
            for attribute in attributes:
                new_attribute = getattr(source, attribute, None)
                if new_attribute is not None:
                    setattr(target, attribute, new_attribute)

        # Update space attributes
        space_attributes = ['clip_end', 'clip_start', 'lens']
        update_attributes(source_space,
                    target_space, space_attributes)
        # Update ViewRegion3D attributes
        # All modifiable attributes
        view_region_3d_attributes = ['clip_planes', 'is_orthographic_side_view', 'is_perspective', 'lock_rotation', 'show_sync_view', 'use_box_clip', 'use_clip_planes',
                                     'view_camera_offset', 'view_camera_zoom', 'view_distance', 'view_location', 'view_perspective', 'view_rotation']
        update_attributes(source_space.region_3d,
                          target_space.region_3d, view_region_3d_attributes)

    # Handle zoom
    if is_zoom:
        print("Before", main_view_space.region_3d.view_distance)
        bpy.ops.view3d.zoom(delta=1 if event.type == 'WHEELUPMOUSE' else -1)
        main_view_space.region_3d.update() # Force the value to be updated
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
                main_view_space.region_3d.update() # Force the value to be updated for zoom
                break
    # print(main_view_space.region_3d.view_distance, main_view_space.region_3d.view_location, main_view_space.region_3d.view_matrix)

    # Now update all 3d viewport spaces
    for area in context.screen.areas:
        # print(area.ui_type)
        if area.ui_type == "VIEW_3D":
            update_space(main_view_space, area.spaces[0])
    print("Viewport Sync Finished: %.4f sec" % (time.time() - time_start))


class TestOperator(bpy.types.Operator):
    """Tooltip"""
    bl_idname = "test.test_modal"
    bl_label = "Test Modal Operator"

    _syncing = False

    # def execute(self, context):

    #     sync_views(context)
    #     return {'FINISHED'}

    def invoke(self, context, event):
        context.window_manager.modal_handler_add(self)
        return {'RUNNING_MODAL'}

    def modal(self, context, event):
        print(event.type, event.value)
        # TODO: Fix alt + middle mouse axis views
        if event.type == 'MIDDLEMOUSE' and event.value == 'PRESS' and not event.alt:
            self._syncing = True
            print("Syncing")
            return {'PASS_THROUGH'}
        elif event.type == 'MOUSEMOVE' and self._syncing:
            sync_views(context, event)
            self._syncing = False
            return {'PASS_THROUGH'}
        elif event.type in {'WHEELUPMOUSE', 'WHEELDOWNMOUSE'} and not (event.alt or event.ctrl or event.shift or event.oskey):
            # Since the zoom operator takes place after this, it will be delayed by one operation if we do not just handle zoom right here
            sync_views(context, event, True)
            return {'RUNNING_MODAL'} # Consume the event and prevent regular zoom from occuring
        elif event.type == "RIGHTMOUSE":
            return {"FINISHED"}
        return {'PASS_THROUGH'}


def menu_func(self, context):
    self.layout.operator(TestOperator.bl_idname, text=TestOperator.bl_label)


# Register and add to the "object" menu (required to also use F3 search "Simple Object Operator" for quick access).
def register():
    bpy.utils.register_class(TestOperator)
    bpy.types.VIEW3D_MT_object.append(menu_func)


def unregister():
    bpy.utils.unregister_class(TestOperator)
    bpy.types.VIEW3D_MT_object.remove(menu_func)


if __name__ == "__main__":
    register()

    # test call
    bpy.ops.object.simple_operator()
