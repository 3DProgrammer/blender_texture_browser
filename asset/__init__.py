import os
import re

from .. import global_vars


class DownloadType:
    resolution: int
    format: str

    def ui_name(self):
        return str(self.resolution) + "K_" + str(self.format)

    def __init__(self, res, fmt):
        self.resolution = res
        self.format = fmt


def infer_dl_type(name):
    result = DownloadType(1, global_vars.IMG_FORMAT_PNG)
    if "png" in name.lower():
        result.format = global_vars.IMG_FORMAT_PNG
    if "jpg" in name.lower():
        result.format = global_vars.IMG_FORMAT_JPG
    if "jpeg" in name.lower():
        result.format = global_vars.IMG_FORMAT_JPG
    if "exr" in name.lower():
        result.format = global_vars.IMG_FORMAT_EXR
    re_result = re.findall("[^0-9]*([0-9]*).*", name)
    if len(re_result) > 0:
        result.resolution = int(re_result[0])
    return result


class Download:
    dl_format: str
    dl_type: DownloadType
    dl_func = None
    urls = []

    def __init__(self, fmt, dl_t, _urls, _func):
        self.dl_format = fmt
        self.dl_type = dl_t
        self.urls = _urls
        self.dl_func = _func

    def __eq__(self, other):
        return self.dl_type.ui_name() == other.dl_type.ui_name()


class Asset:
    source: str
    name: str
    fancyName: str
    downloads = []
    preview_url: str
    tags = []

    def full_name(self):
        return self.source + "_" + self.name

    def preview_path(self):
        return os.path.join(os.path.join(global_vars.cache_dir, "previews"), self.full_name() + ".png")

    def cache_path(self, dl: DownloadType):
        return os.path.join(os.path.join(os.path.join(global_vars.cache_dir, "downloads"), self.full_name()),
                            dl.ui_name())

    def has_tag(self, tg):
        return tg in self.tags

    def __init__(self, src, nm, fnm, dls, p_url, tgs):
        self.source = src
        self.name = nm
        self.fancyName = fnm
        self.downloads = dls
        self.preview_url = p_url
        self.tags = tgs

    def __eq__(self, other):
        return type(self) == type(other) and self.full_name() == other.full_name()
