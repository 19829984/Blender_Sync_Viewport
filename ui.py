import bpy


def menu_func(self, context):
    layout = self.layout
    view_region = context.area.spaces[0].region_3d
    # Disable if in quadview
    if len(context.space_data.region_quadviews) <= 1:
        layout.prop(view_region, "show_sync_view", text="", icon_only=True, icon="UV_SYNC_SELECT")


def register():
    bpy.types.VIEW3D_HT_header.append(menu_func)


def unregister():
    bpy.types.VIEW3D_HT_header.remove(menu_func)
