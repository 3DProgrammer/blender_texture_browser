import os

import requests

from .. import global_vars
from . import ambientcg


def load():
    for asset in ambientcg.load():
        if asset not in global_vars.assets:
            global_vars.assets.append(asset)
        preview_path = os.path.join(os.path.join(global_vars.cache_dir, "previews"), asset.full_name() + ".png")
        if not os.path.isfile(preview_path):
            data = requests.get(asset.preview_url, headers={'User-Agent': "Python"}).content
            f = open(preview_path, "wb")
            f.write(data)
            f.close()
        if not asset.full_name() in global_vars.preview_collections["main"]:
            global_vars.preview_collections["main"].load(asset.full_name(), preview_path,
                                                         "IMAGE")