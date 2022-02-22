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
from . import loader

bl_info = {
	"name": "Texture Browser",
	"blender": (3, 00, 0),
	"version": (1, 1),
	"category": "Material",
}

colour_space = {"Metal": "Non-Color", "Rough": "Non-Color", "Normal": "Non-Color", "Colour": "sRGB",
				"Disp": "Non-Color", "Emit": "sRGB"}


class SetMaterial(bpy.types.Operator):
	"""Sets the material for the object"""
	bl_idname = "object.tex_browser_set_mat"
	bl_label = "Set Material From Texture Browser"
	bl_options = {"REGISTER", "UNDO"}
	mat_name: bpy.props.StringProperty(name="Material name")
	dl_type: bpy.props.StringProperty(name="Resolution and format", default="1K-PNG")

	def execute(self, context):
		next_asset = None
		for i in global_vars.assets:
			if i.full_name() == self.mat_name:
				next_asset = i
				break
		if next_asset is None:
			return {"FINISHED"}  # This should never happen.
		asset_dl_type = None
		for i in next_asset.downloads:
			if i.dl_type.ui_name() == self.dl_type:
				asset_dl_type = i
				break
		if asset_dl_type is None:
			return {"FINISHED"}  # This should never happen
		# The download function should place the assets in the cache path with the following names:
		# Metal, Rough, Normal, Colour, Disp, Emit
		cache_path = os.path.join(
			os.path.join(os.path.join(global_vars.cache_dir, "downloads"), next_asset.full_name()),
			asset_dl_type.dl_type.ui_name())
		if not os.path.isdir(cache_path):
			os.makedirs(cache_path, mode=0o744)
			asset_dl_type.dl_func(next_asset, asset_dl_type, cache_path)
		m = bpy.data.materials.new(next_asset.fancyName)
		m.use_nodes = True
		nt = m.node_tree
		pbsdf = nt.nodes["Principled BSDF"]
		tc = nt.nodes.new(type="ShaderNodeTexCoord")
		mp = nt.nodes.new(type="ShaderNodeMapping")
		nt.links.new(tc.outputs["UV"], mp.inputs["Vector"])
		for i in os.listdir(cache_path):
			if next_asset.full_name() + i in bpy.data.images:
				img = bpy.data.images[next_asset.full_name() + i]
			else:
				img = bpy.data.images.load(os.path.join(cache_path, i))
				img.name = next_asset.full_name() + i
			node = nt.nodes.new(type="ShaderNodeTexImage")
			nt.links.new(mp.outputs["Vector"], node.inputs["Vector"])
			node.image = img
			map_type = re.findall(r"(.*)\.", i)[0]
			img.colorspace_settings.name = colour_space[map_type]
			if map_type == "Colour":
				nt.links.new(node.outputs["Color"], pbsdf.inputs["Base Color"])
			elif map_type == "Disp":
				dp = nt.nodes.new(type="ShaderNodeDisplacement")
				nt.links.new(node.outputs["Color"], dp.inputs["Height"])
				nt.links.new(dp.outputs["Displacement"], nt.nodes["Material Output"].inputs["Displacement"])
			elif map_type == "Metal":
				nt.links.new(node.outputs["Color"], pbsdf.inputs["Metallic"])
			elif map_type == "Normal":
				nm = nt.nodes.new(type="ShaderNodeNormalMap")
				nt.links.new(node.outputs["Color"], nm.inputs["Color"])
				nt.links.new(nm.outputs["Normal"], pbsdf.inputs["Normal"])
			elif map_type == "Rough":
				nt.links.new(node.outputs["Color"], pbsdf.inputs["Roughness"])
			elif map_type == "Emit":
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
		loader.load()
		write_cache()
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
	# if os.path.isfile(os.path.join(cache_path, "mat_cache")):
	#     f = open(os.path.join(cache_path, "mat_cache"), "r")
	#     global_vars.cache = json.loads(f.read())
	#     f.close()
	if os.path.isfile(os.path.join(cache_path, "asset_cache")):
		f = open(os.path.join(cache_path, "asset_cache"), "rb")
		global_vars.assets = pickle.loads(f.read())
		f.close()
	if os.path.isfile(os.path.join(cache_path, "tag_cache")):
		f = open(os.path.join(cache_path, "tag_cache"), "rb")
		global_vars.tags = pickle.loads(f.read())
		f.close()
	if global_vars.assets is not None:
		for i in global_vars.assets:
			if not os.path.isfile(i.preview_path()):
				image = requests.get(i.preview_url)
				f = open(i.preview_path(), "wb")
				f.write(image.content)
				f.close()
			global_vars.preview_collections["main"].load(i.full_name(),
														 i.preview_path(),
														 "IMAGE")


def write_cache():
	cache_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), "cache")
	# f = open(os.path.join(cache_path, "mat_cache"), "w")
	# f.write(json.dumps(global_vars.cache))
	# f.close()
	f = open(os.path.join(cache_path, "tag_cache"), "wb")
	f.write(pickle.dumps(global_vars.tags))
	f.close()
	f = open(os.path.join(cache_path, "asset_cache"), "wb")
	f.write(pickle.dumps(global_vars.assets))
	f.close()


classes = [TagPropertyGroup, FilterSettings, ui.NextPage, ui.PrevPage, SetMaterial, ui.MaterialSwitcherPanel,
		   ui.FilterPanel,
		   ui.FilterNamePanel, ui.FilterTagPanel, ui.MatBrowserPanel, RefreshCache, RefreshTags]


def register():
	global_vars.cache_dir = os.path.join(os.path.dirname(os.path.realpath(__file__)), "cache")
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
