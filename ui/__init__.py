import os

import bpy
import math
from .. import global_vars
from .. import asset


class NextPage(bpy.types.Operator):
    """Moves to the next page in the texture browser"""
    bl_idname = "material.tex_browser_next_page"
    bl_label = "Next Page"
    bl_options = {"INTERNAL", "REGISTER"}

    def execute(self, context):
        num_pages = math.ceil(float(len(global_vars.assets)) / float(global_vars.pageSize))
        if global_vars.page < num_pages - 1:
            global_vars.page += 1
        return {"FINISHED"}


class PrevPage(bpy.types.Operator):
    """Moves to the previous page in the texture browser"""
    bl_idname = "material.tex_browser_prev_page"
    bl_label = "Previous Page"
    bl_options = {"INTERNAL", "REGISTER"}

    def execute(self, context):
        if global_vars.page > 0:
            global_vars.page -= 1
        return {"FINISHED"}


class MaterialSwitcherPanel(bpy.types.Panel):
    bl_label = "Material Browser"
    bl_idname = "OBJECT_PT_mat_switcher"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "material"

    def draw(self, context):
        layout = self.layout
        if len(global_vars.assets) == 0:
            row = layout.row()
            row.label(text="Cache is empty", icon="ERROR")
        row = layout.row()
        row.operator("material.tex_browser_refresh_cache")


# def filter_by_name(name, inputs: list):
#     result = []
#     for i in inputs:
#         if name.lower() in i.lower() or name.lower() in global_vars.cache[i]["displayName"].lower():
#             result.append(i)
#     return result


# def filter_by_tag(tag, inputs: list):
#     result = []
#     for i in inputs:
#         for j in global_vars.cache[i]['tags']:
#             if tag.lower() == j.lower():
#                 result.append(i)
#                 break
#     return result


class MatBrowserPanel(bpy.types.Panel):
    bl_parent_id = "OBJECT_PT_mat_switcher"
    bl_label = "Material Browser"
    bl_idname = "OBJECT_PT_mat_browser"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "material"
    bl_options = {"HIDE_HEADER"}

    def draw(self, context):
        layout = self.layout
        # keys = list(global_vars.cache.keys())
        # if context.scene.mat_browser_filter_settings.filter_name_bool:
        #     keys = filter_by_name(context.scene.mat_browser_filter_settings.filter_name_str, keys)
        # if context.scene.mat_browser_filter_settings.filter_tag_bool:
        #     for i in context.scene.mat_browser_filter_settings.tag_props:
        #         if i.filter_tag:
        #             keys = filter_by_tag(i.tag_name, keys)
        # keys.sort()
        assets = []
        for i in global_vars.assets:
            assets.append(i)  # TODO: Filter assets.
        row = layout.row()
        row.operator("material.tex_browser_prev_page", text="", translate=False, icon="TRIA_LEFT")
        row.label(text="Page " + str(global_vars.page + 1) + "/" + str(
            math.ceil(float(len(assets)) / float(global_vars.pageSize))))
        row.operator("material.tex_browser_next_page", text="", translate=False, icon="TRIA_RIGHT")
        box = layout.box()
        grid = box.grid_flow(even_columns=True, even_rows=True)
        startIndex = global_vars.page * global_vars.pageSize
        endIndex = min(startIndex + global_vars.pageSize, len(assets))
        assets = assets[startIndex:endIndex]
        for i in assets:
            c = grid.box()
            c.template_icon(icon_value=global_vars.preview_collections["main"][i.full_name()].icon_id, scale=5)
            types = i.downloads
            c.label(text=i.fancyName, translate=False)
            png_row = c.row()
            jpg_row = c.row()
            exr_row = c.row()
            png = False
            jpg = False
            exr = False
            for dltype in types:
                row = None
                if dltype.dl_type.format == global_vars.IMG_FORMAT_PNG:
                    if not png:
                        png_row.label(text="PNG:")
                        png = True
                    row = png_row
                if dltype.dl_type.format == global_vars.IMG_FORMAT_JPG:
                    if not jpg:
                        jpg_row.label(text="JPG:")
                        jpg = True
                    row = jpg_row
                if dltype.dl_type.format == global_vars.IMG_FORMAT_EXR:
                    if not exr:
                        exr_row.label(text="EXR:")
                        exr = True
                    row = exr_row
                if os.path.isdir(i.cache_path(dltype.dl_type)):  # TODO: Better cache detection
                    button = row.operator("object.tex_browser_set_mat", text=dltype.dl_type.ui_name(),
                                          icon="DISK_DRIVE")
                else:
                    button = row.operator("object.tex_browser_set_mat", text=dltype.dl_type.ui_name())
                button.mat_name = i.full_name()
                button.dl_type = dltype.dl_type.ui_name()


class FilterPanel(bpy.types.Panel):
    bl_parent_id = "OBJECT_PT_mat_switcher"
    bl_idname = "OBJECT_PT_mat_browser_filter"
    bl_label = "Filter"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_options = {"DEFAULT_CLOSED"}

    def draw(self, context):
        layout = self.layout


class FilterNamePanel(bpy.types.Panel):
    bl_parent_id = "OBJECT_PT_mat_browser_filter"
    bl_idname = "OBJECT_PT_mat_browser_filter_name"
    bl_label = "Name"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_options = {"DEFAULT_CLOSED"}

    def draw(self, context):
        layout = self.layout
        layout.prop(context.scene.mat_browser_filter_settings, "filter_name_str", text="")

    def draw_header(self, context):
        self.layout.prop(context.scene.mat_browser_filter_settings, "filter_name_bool", text="")


class FilterTagPanel(bpy.types.Panel):
    bl_parent_id = "OBJECT_PT_mat_browser_filter"
    bl_idname = "OBJECT_PT_mat_browser_filter_tag"
    bl_label = "Tags"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_options = {"DEFAULT_CLOSED"}

    def draw(self, context):
        layout = self.layout
        layout.operator("material.tex_browser_refresh_tags")
        layout.prop(context.scene.mat_browser_filter_settings, "tag_search", text="", icon="VIEWZOOM")
        c = layout.grid_flow(columns=4, even_columns=True, even_rows=True)
        for i in context.scene.mat_browser_filter_settings.tag_props:
            if context.scene.mat_browser_filter_settings.tag_search.lower() in i.tag_name.lower():
                r = c.box().row()
                r.prop(i, "filter_tag", text="")
                r.label(text=i.tag_name)

    def draw_header(self, context):
        self.layout.prop(context.scene.mat_browser_filter_settings, "filter_tag_bool", text="")
