import io
import re
import zipfile

from .. import asset
from .. import global_vars
import requests
import os

translations = {"Diffuse": "Colour", "Displacement": "Disp", "#####": "Emit", "Metal": "Metal",
				"nor_gl": "Normal", "Rough": "Rough"}


def download_polyhaven(dl_asset: asset.Asset, dl_type: asset.Download, cache_path):
	dl_data = dl_type.urls
	for i in translations:
		if i in dl_data:
			dl_link = dl_data[i][str(dl_type.dl_type.resolution) + "k"][dl_type.dl_type.format.lower()]['url']
			print(dl_link)
			f = open(os.path.join(cache_path, translations[i]+"."+dl_type.dl_type.format.lower()), "wb")
			f.write(requests.get(dl_link).content)
			f.close()



def load():
	new_assets = []
	data = requests.get("https://api.polyhaven.com/assets?t=textures").json()
	for new_asset_name in list(data):
		print("Downloading asset " + new_asset_name)
		dl_data = requests.get("https://api.polyhaven.com/files/" + new_asset_name).json()
		info_data = requests.get("https://api.polyhaven.com/info/" + new_asset_name).json()
		asset_tags = set()
		for i in info_data['tags']:
			asset_tags.add(i.lower())
			global_vars.tags.add(i.lower())
		for i in info_data['categories']:
			asset_tags.add(i.lower())
			global_vars.tags.add(i.lower())
		asset_dls = []
		for i in ['Diffuse', 'Rough', 'Displacement', 'Metal', 'nor_gl']:
			if i in dl_data:
				for res in dl_data[i]:
					for img_format in dl_data[i][res]:
						print(asset.infer_dl_type(res + img_format).format,
							  str(asset.infer_dl_type(res + img_format).resolution) + 'K')
						asset_dls.append(
							asset.Download(global_vars.DL_FORMAT_MANY, asset.infer_dl_type(res + img_format), dl_data,
										   download_polyhaven))
				break
		new_assets.append(asset.Asset(global_vars.ASSET_SOURCE_POLYHAVEN, new_asset_name, info_data['name'], asset_dls,
									  "https://cdn.polyhaven.com/asset_img/thumbs/" + new_asset_name + ".png?width=255&height=255&format=png",
									  list(asset_tags)))

	return new_assets
