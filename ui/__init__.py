import bpy
import math
from .. import global_vars
from .. import asset

page = 0
pageSize = 25


class NextPage(bpy.types.Operator):
    """Moves to the next page in the texture browser"""
    bl_idname = "material.tex_browser_next_page"
    bl_label = "Next Page"
    bl_options = {"INTERNAL", "REGISTER"}

    def execute(self, context):
        global page
        global pageSize
        num_pages = math.ceil(float(len(global_vars.cache)) / float(pageSize))
        if page < num_pages - 1:
            page += 1
        return {"FINISHED"}


class PrevPage(bpy.types.Operator):
    """Moves to the previous page in the texture browser"""
    bl_idname = "material.tex_browser_prev_page"
    bl_label = "Previous Page"
    bl_options = {"INTERNAL", "REGISTER"}

    def execute(self, context):
        global page
        if page > 0:
            page -= 1
        return {"FINISHED"}


class MaterialSwitcherPanel(bpy.types.Panel):
    bl_label = "Material Browser"
    bl_idname = "OBJECT_PT_mat_switcher"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "material"

    def draw(self, context):
        layout = self.layout
        if not global_vars.cache:
            row = layout.row()
            row.label(text="Cache is empty", icon="ERROR")
        row = layout.row()
        row.operator("material.tex_browser_refresh_cache")


def filter_by_name(name, inputs: list):
    result = []
    for i in inputs:
        if name.lower() in i.lower() or name.lower() in global_vars.cache[i]["displayName"].lower():
            result.append(i)
    return result


def filter_by_tag(tag, inputs: list):
    result = []
    for i in inputs:
        for j in global_vars.cache[i]['tags']:
            if tag.lower() == j.lower():
                result.append(i)
                break
    return result


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
        keys = list(global_vars.cache.keys())
        if context.scene.mat_browser_filter_settings.filter_name_bool:
            keys = filter_by_name(context.scene.mat_browser_filter_settings.filter_name_str, keys)
        if context.scene.mat_browser_filter_settings.filter_tag_bool:
            for i in context.scene.mat_browser_filter_settings.tag_props:
                if i.filter_tag:
                    keys = filter_by_tag(i.tag_name, keys)
        keys.sort()
        row = layout.row()
        row.operator("material.tex_browser_prev_page", text="", translate=False, icon="TRIA_LEFT")
        row.label(text="Page " + str(page + 1) + "/" + str(math.ceil(float(len(keys)) / float(pageSize))))
        row.operator("material.tex_browser_next_page", text="", translate=False, icon="TRIA_RIGHT")
        box = layout.box()
        grid = box.grid_flow(even_columns=True, even_rows=True)
        startIndex = page * pageSize
        endIndex = min(startIndex + pageSize, len(keys))
        keys = keys[startIndex:endIndex]
        for i in keys:
            c = grid.box()
            c.template_icon(icon_value=global_vars.preview_collections["main"][i].icon_id, scale=5)
            types = asset.get_types(global_vars.cache[i])
            c.label(text=global_vars.cache[i]["displayName"], translate=False)
            for x in types:
                r = c.row()
                if len(x) > 0:
                    r.label(text=x[0][2][-3:] + ":")
                    for y in x:
                        if y[1]:
                            props = r.operator("object.tex_browser_set_mat", text=str(y[0]) + "K", translate=False,
                                               icon="DISK_DRIVE")
                        else:
                            props = r.operator("object.tex_browser_set_mat", text=str(y[0]) + "K", translate=False)
                        props.mat_name = i
                        props.mat_type = y[2]


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
