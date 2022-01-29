import math
import pickle
import re
import zipfile
from copy import copy

import bpy
import requests
import bpy.utils.previews
import json
import os

bl_info = {
    "name": "Material Browser",
    "blender": (3, 00, 0),
    "version": (1, 0),
    "category": "Material",
}
addon_keymaps = []
cache = {}
preview_collections = {}
tags: set = set()


def get_types(material):
    result = [[], []]
    name = material["assetId"]
    if "zip" in material["downloadFolders"]["/"]["downloadFiletypeCategories"]:
        for i in material["downloadFolders"]["/"]["downloadFiletypeCategories"]["zip"]["downloads"]:
            cache_path = os.path.join(os.path.join(os.path.join(os.path.dirname(os.path.realpath(__file__)), "cache"
                                                                                                             "/downloads"),
                                                   name), i["attribute"])
            # print(cache_path)
            if i["attribute"] == "2kPNG-PNG":
                i["attribute"] = "2K-PNG"
            if i["attribute"] == "1kPNG-PNG":
                i["attribute"] = "1K-PNG"
            if i["attribute"] == "4kPNG-PNG":
                i["attribute"] = "4K-PNG"
            if i["attribute"] == "8kPNG-PNG":
                i["attribute"] = "8K-PNG"
            if i["attribute"] == "1kPNG":
                i["attribute"] = "1K-PNG"
            if i["attribute"] == "2kPNG":
                i["attribute"] = "2K-PNG"
            if i["attribute"] == "4kPNG":
                i["attribute"] = "4K-PNG"
            if i["attribute"] == "8kPNG":
                i["attribute"] = "8K-PNG"
            if len(i["attribute"]) > 0:
                next_element = (int(i["attribute"][:-5]), os.path.isdir(cache_path), i["attribute"])
                if "PNG" in i["attribute"]:
                    result[0].append(next_element)
                elif "JPG" in i["attribute"]:
                    result[1].append(next_element)
        result[0].sort()
        result[1].sort()
    return result


mapswanted = {"Color": "sRGB", "Displacement": "Non-Color", "Metalness": "Non-Color", "NormalGL": "Non-Color",
              "Roughness": "Non-Color"}


class SetMaterial(bpy.types.Operator):
    """Sets the material for the object"""
    bl_idname = "object.tex_browser_set_mat"
    bl_label = "Set Material From Texture Browser"
    bl_options = {"REGISTER", "UNDO"}
    mat_name: bpy.props.StringProperty(name="Material name")
    mat_type: bpy.props.StringProperty(name="Resolution and format", default="1K-PNG")

    def execute(self, context):
        cache_path = os.path.join(
            os.path.join(os.path.join(os.path.dirname(os.path.realpath(__file__)), "cache/downloads"),
                         self.mat_name), self.mat_type)
        if not os.path.isdir(cache_path):
            os.makedirs(cache_path, mode=0o744)
            for i in cache[self.mat_name]["downloadFolders"]["/"]["downloadFiletypeCategories"]["zip"]["downloads"]:
                if i["attribute"] == self.mat_type:
                    data = requests.get(i["downloadLink"], headers={'User-Agent': "Python"}).content
                    f = open(os.path.join(cache_path, self.mat_type + ".zip"), "wb")
                    f.write(data)
                    f.close()
                    with zipfile.ZipFile(os.path.join(cache_path, self.mat_type + ".zip"), "r") as zip_ref:
                        zip_ref.extractall(cache_path)
                    for x in os.listdir(cache_path):
                        found = False
                        for y in mapswanted.keys():
                            if y in x:
                                found = True
                                break
                        if not found:
                            os.remove(os.path.join(cache_path, x))
                    break
        m = bpy.data.materials.new(self.mat_name)
        m.use_nodes = True
        nt = m.node_tree
        pbsdf = nt.nodes["Principled BSDF"]
        tc = nt.nodes.new(type="ShaderNodeTexCoord")
        mp = nt.nodes.new(type="ShaderNodeMapping")
        nt.links.new(tc.outputs["UV"], mp.inputs["Vector"])
        for i in os.listdir(cache_path):
            if i not in bpy.data.images:
                bpy.data.images.load(os.path.join(cache_path, i))
            img = bpy.data.images[i]
            node = nt.nodes.new(type="ShaderNodeTexImage")
            nt.links.new(mp.outputs["Vector"], node.inputs["Vector"])
            node.image = img
            map_type = re.findall(r".*_(.*)\.", i)[0]
            img.colorspace_settings.name = mapswanted[map_type]
            if map_type == "Color":
                nt.links.new(node.outputs["Color"], pbsdf.inputs["Base Color"])
            elif map_type == "Displacement":
                dp = nt.nodes.new(type="ShaderNodeDisplacement")
                nt.links.new(node.outputs["Color"], dp.inputs["Height"])
                nt.links.new(dp.outputs["Displacement"], nt.nodes["Material Output"].inputs["Displacement"])
            elif map_type == "Metalness":
                nt.links.new(node.outputs["Color"], pbsdf.inputs["Metallic"])
            elif map_type == "NormalGL":
                nm = nt.nodes.new(type="ShaderNodeNormalMap")
                nt.links.new(node.outputs["Color"], nm.inputs["Color"])
                nt.links.new(nm.outputs["Normal"], pbsdf.inputs["Normal"])
            elif map_type == "Roughness":
                nt.links.new(node.outputs["Color"], pbsdf.inputs["Roughness"])
        for i in context.selected_objects:
            if i.type == "MESH" or i.type == "CURVE":
                if len(i.material_slots) == 0:
                    i.data.materials.append(m)
                else:
                    i.material_slots[0].material = m
        return {"FINISHED"}


class RefreshCache(bpy.types.Operator):
    """Refreshes the material cache"""
    bl_idname = "material.tex_browser_refresh_cache"
    bl_label = "Refresh Cache"
    bl_options = {"REGISTER"}

    def execute(self, context):
        data = {
            "nextPageHttp": "https://ambientcg.com/api/v2/full_json?type=PhotoTexturePBR&limit=100&include"
                            "=downloadData,imageData,displayData,tagData"}
        while data["nextPageHttp"]:
            print(data["nextPageHttp"])
            data = requests.get(
                data["nextPageHttp"],
                headers={'User-Agent': "Python"}).json()
            for asset in data["foundAssets"]:
                for i in asset['tags']:
                    tags.add(i.lower())
                if not asset['assetId'] in cache:
                    cache[asset['assetId']] = asset
                    filepath = os.path.join(
                        os.path.join(os.path.join(os.path.dirname(os.path.realpath(__file__)), "cache"), "previews"),
                        asset["assetId"] + ".png")
                    if not os.path.isfile(filepath):
                        image = requests.get(asset["previewImage"]["128-PNG"])
                        f = open(filepath, "wb")
                        f.write(image.content)
                        f.close()
                    preview_collections["main"].load(asset['assetId'], filepath,
                                                     "IMAGE")
        write_cache()
        bpy.ops.material.tex_browser_refresh_tags()
        return {"FINISHED"}


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
        num_pages = math.ceil(float(len(cache)) / float(pageSize))
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
        if not cache:
            row = layout.row()
            row.label(text="Cache is empty", icon="ERROR")
        row = layout.row()
        row.operator("material.tex_browser_refresh_cache")


def filter_by_name(name, inputs: list):
    result = []
    for i in inputs:
        if name.lower() in i.lower() or name.lower() in cache[i]["displayName"].lower():
            result.append(i)
    return result


def filter_by_tag(tag, inputs: list):
    result = []
    for i in inputs:
        for j in cache[i]['tags']:
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
        keys = list(cache.keys())
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
            c.template_icon(icon_value=preview_collections["main"][i].icon_id, scale=5)
            types = get_types(cache[i])
            c.label(text=cache[i]["displayName"], translate=False)
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


class RefreshTags(bpy.types.Operator):
    """Loads Tags"""
    bl_idname = "material.tex_browser_refresh_tags"
    bl_label = "Load Tags"
    bl_options = {"INTERNAL", "REGISTER"}

    def execute(self, context):
        list_tags = list(tags)
        list_tags.sort()
        if len(list_tags) > len(context.scene.mat_browser_filter_settings.tag_props):
            context.scene.mat_browser_filter_settings.tag_props.clear()
            for i in list_tags:
                newItem = context.scene.mat_browser_filter_settings.tag_props.add()
                newItem.tag_name = i
        return {"FINISHED"}


class TagPropertyGroup(bpy.types.PropertyGroup):
    tag_name: bpy.props.StringProperty()
    filter_tag: bpy.props.BoolProperty()


class FilterSettings(bpy.types.PropertyGroup):
    filter_name_bool: bpy.props.BoolProperty(name="Filter By Name", description="Filter Materials By Name",
                                             default=False)

    filter_tag_bool: bpy.props.BoolProperty(name="Filter By Tag", description="Filter Materials By Tag",
                                            default=False)
    filter_name_str: bpy.props.StringProperty(name="Name", description="Name To Filter Materials By", default="")
    tag_search: bpy.props.StringProperty(name="Search", description="Search Tags", default="")
    tag_props: bpy.props.CollectionProperty(type=TagPropertyGroup)


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


def read_cache():
    global cache
    global tags
    cache_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), "cache")
    if os.path.isfile(os.path.join(cache_path, "mat_cache")):
        f = open(os.path.join(cache_path, "mat_cache"), "r")
        cache = json.loads(f.read())
        f.close()
    if os.path.isfile(os.path.join(cache_path, "tag_cache")):
        f = open(os.path.join(cache_path, "tag_cache"), "rb")
        tags = pickle.loads(f.read())
        f.close()
    if cache is not None:
        for i in cache:
            if not os.path.isfile(os.path.join(os.path.join(cache_path, "previews"), i + ".png")):
                image = requests.get(cache[i]["previewImage"]["128-PNG"])
                f = open(os.path.join(os.path.join(cache_path, "previews"), i + ".png"), "wb")
                f.write(image.content)
                f.close()
            preview_collections["main"].load(i, os.path.join(os.path.join(cache_path, "previews"), i + ".png"),
                                             "IMAGE")


def write_cache():
    cache_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), "cache")
    f = open(os.path.join(cache_path, "mat_cache"), "w")
    f.write(json.dumps(cache))
    f.close()
    f = open(os.path.join(cache_path, "tag_cache"), "wb")
    f.write(pickle.dumps(tags))
    f.close()


def register():
    pcoll = bpy.utils.previews.new()
    preview_collections["main"] = pcoll
    bpy.utils.register_class(TagPropertyGroup)
    bpy.utils.register_class(FilterSettings)
    bpy.utils.register_class(NextPage)
    bpy.utils.register_class(PrevPage)
    bpy.utils.register_class(SetMaterial)
    bpy.utils.register_class(MaterialSwitcherPanel)
    bpy.utils.register_class(FilterPanel)
    bpy.utils.register_class(FilterNamePanel)
    bpy.utils.register_class(FilterTagPanel)
    bpy.utils.register_class(MatBrowserPanel)
    bpy.utils.register_class(RefreshCache)
    bpy.utils.register_class(RefreshTags)
    bpy.types.Scene.mat_browser_filter_settings = bpy.props.PointerProperty(type=FilterSettings)
    read_cache()


def unregister():
    bpy.utils.unregister_class(TagPropertyGroup)
    bpy.utils.unregister_class(FilterSettings)
    bpy.utils.unregister_class(NextPage)
    bpy.utils.unregister_class(PrevPage)
    bpy.utils.unregister_class(SetMaterial)
    bpy.utils.unregister_class(MaterialSwitcherPanel)
    bpy.utils.unregister_class(RefreshCache)
    bpy.utils.unregister_class(FilterPanel)
    bpy.utils.unregister_class(FilterNamePanel)
    bpy.utils.unregister_class(FilterTagPanel)
    bpy.utils.unregister_class(MatBrowserPanel)
    bpy.utils.unregister_class(RefreshTags)
    del bpy.types.Scene.mat_browser_filter_settings


if __name__ == "__main__":
    register()
