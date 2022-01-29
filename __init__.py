import math
import pickle
import re
import zipfile
import bpy
import requests
import bpy.utils.previews
import json
import os
from . import global_vars
from . import ui
from . import asset

bl_info = {
    "name": "Material Browser",
    "blender": (3, 00, 0),
    "version": (1, 0),
    "category": "Material",
}

mapswanted = {"Color": "sRGB", "Displacement": "Non-Color", "Metalness": "Non-Color", "NormalGL": "Non-Color",
              "Roughness": "Non-Color", "Emission": "sRGB"}


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
            for i in global_vars.cache[self.mat_name]["downloadFolders"]["/"]["downloadFiletypeCategories"]["zip"][
                "downloads"]:
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
            elif map_type == "Emission":
                nt.links.new(node.outputs["Color"], pbsdf.inputs["Emission"])
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
            for next_asset in data["foundAssets"]:
                for i in next_asset['tags']:
                    global_vars.tags.add(i.lower())
                if not next_asset['assetId'] in global_vars.cache:
                    global_vars.cache[next_asset['assetId']] = next_asset
                    filepath = os.path.join(
                        os.path.join(os.path.join(os.path.dirname(os.path.realpath(__file__)), "cache"), "previews"),
                        next_asset["assetId"] + ".png")
                    if not os.path.isfile(filepath):
                        image = requests.get(next_asset["previewImage"]["128-PNG"])
                        f = open(filepath, "wb")
                        f.write(image.content)
                        f.close()
                    global_vars.preview_collections["main"].load(next_asset['assetId'], filepath,
                                                                 "IMAGE")
        write_cache()
        bpy.ops.material.tex_browser_refresh_tags()
        return {"FINISHED"}


class RefreshTags(bpy.types.Operator):
    """Loads Tags"""
    bl_idname = "material.tex_browser_refresh_tags"
    bl_label = "Load Tags"
    bl_options = {"INTERNAL", "REGISTER"}

    def execute(self, context):
        list_tags = list(global_vars.tags)
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


def read_cache():
    cache_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), "cache")
    if os.path.isfile(os.path.join(cache_path, "mat_cache")):
        f = open(os.path.join(cache_path, "mat_cache"), "r")
        global_vars.cache = json.loads(f.read())
        f.close()
    if os.path.isfile(os.path.join(cache_path, "tag_cache")):
        f = open(os.path.join(cache_path, "tag_cache"), "rb")
        global_vars.tags = pickle.loads(f.read())
        f.close()
    if global_vars.cache is not None:
        for i in global_vars.cache:
            if not os.path.isfile(os.path.join(os.path.join(cache_path, "previews"), i + ".png")):
                image = requests.get(global_vars.cache[i]["previewImage"]["128-PNG"])
                f = open(os.path.join(os.path.join(cache_path, "previews"), i + ".png"), "wb")
                f.write(image.content)
                f.close()
            global_vars.preview_collections["main"].load(i,
                                                         os.path.join(os.path.join(cache_path, "previews"), i + ".png"),
                                                         "IMAGE")


def write_cache():
    cache_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), "cache")
    f = open(os.path.join(cache_path, "mat_cache"), "w")
    f.write(json.dumps(global_vars.cache))
    f.close()
    f = open(os.path.join(cache_path, "tag_cache"), "wb")
    f.write(pickle.dumps(global_vars.tags))
    f.close()


classes = [TagPropertyGroup, FilterSettings, ui.NextPage, ui.PrevPage, SetMaterial, ui.MaterialSwitcherPanel,
           ui.FilterPanel,
           ui.FilterNamePanel, ui.FilterTagPanel, ui.MatBrowserPanel, RefreshCache, RefreshTags]


def register():
    pcoll = bpy.utils.previews.new()
    global_vars.preview_collections["main"] = pcoll
    for i in classes:
        bpy.utils.register_class(i)
    bpy.types.Scene.mat_browser_filter_settings = bpy.props.PointerProperty(type=FilterSettings)
    read_cache()


def unregister():
    for i in classes:
        bpy.utils.unregister_class(i)
    del bpy.types.Scene.mat_browser_filter_settings


if __name__ == "__main__":
    register()
