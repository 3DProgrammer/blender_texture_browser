import io
import re
import zipfile

from .. import asset
from .. import global_vars
import requests
import os

translations = {"Color": "Colour", "Displacement": "Disp", "Emission": "Emit", "Metalness": "Metal",
                "NormalGL": "Normal", "Roughness": "Rough"}


def download_ambientCG(dl_asset: asset.Asset, dl_type: asset.Download, cache_path):
    zip_file = zipfile.ZipFile(io.BytesIO(requests.get(dl_type.urls[0], headers={'User-Agent': "Python"}).content))
    for i in zip_file.namelist():
        regex_match = re.findall(r".*_([a-zA-Z]+)\.[^.]+", i)
        if len(regex_match) > 0:
            map_name = regex_match[0]
            if map_name in translations.keys():
                f = open(os.path.join(cache_path, translations[map_name] + "." + dl_type.dl_type.format.lower()), "wb")
                f.write(zip_file.read(i))
                f.close()


def load():
    new_assets = []
    data = {
        "nextPageHttp": "https://ambientcg.com/api/v2/full_json?type=PhotoTexturePBR&limit=100&include"
                        "=downloadData,imageData,displayData,tagData"}
    while data["nextPageHttp"]:
        print(data["nextPageHttp"])
        data = requests.get(
            data["nextPageHttp"],
            headers={'User-Agent': "Python"}).json()
        for next_asset in data["foundAssets"]:
            asset_tags = set()
            for i in next_asset['tags']:
                asset_tags.add(i.lower())
                global_vars.tags.add(i.lower())  # TODO: Refactor tags.
            asset_dls = []
            if "zip" in next_asset["downloadFolders"]["/"]["downloadFiletypeCategories"]:
                for i in next_asset["downloadFolders"]["/"]["downloadFiletypeCategories"]["zip"]["downloads"]:
                    asset_dls.append(
                        asset.Download(global_vars.DL_FORMAT_ZIP, asset.infer_dl_type(i["attribute"]), [i["downloadLink"]],
                                       download_ambientCG))

                new_assets.append(asset.Asset(global_vars.ASSET_SOURCE_AMBIENTCG, next_asset['assetId'],
                                              next_asset['displayName'], asset_dls, next_asset["previewImage"]["128-PNG"],
                                              list(asset_tags)))

    return new_assets
