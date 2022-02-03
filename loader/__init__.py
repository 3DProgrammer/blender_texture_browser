import os

import requests

from .. import global_vars
from . import ambientcg


def load():
    for asset in ambientcg.load():
        if asset not in global_vars.assets:
            global_vars.assets.append(asset)
        if not os.path.isfile(asset.preview_path()):
            print(asset.preview_url)
            data = requests.get(asset.preview_url, headers={'User-Agent': "Python"}).content
            f = open(asset.preview_path(), "wb")
            f.write(data)
            f.close()
        if not asset.full_name() in global_vars.preview_collections["main"]:
            global_vars.preview_collections["main"].load(asset.full_name(), asset.preview_path(),
                                                         "IMAGE")
