from .. import asset
from .. import global_vars
import requests
import os


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
            for i in next_asset["downloadFolders"]["/"]["downloadFiletypeCategories"]["zip"]["downloads"]:
                asset_dls.append(
                    asset.Download(global_vars.DL_FORMAT_ZIP, asset.infer_dl_type(i["attribute"]), [i["downloadPath"]]))

            new_assets.append(asset.Asset(global_vars.ASSET_SOURCE_AMBIENTCG, next_asset['assetId'],
                                          next_asset['displayName'], asset_dls, next_asset["previewImage"]["128-PNG"],
                                          list(asset_tags)))


    return new_assets
