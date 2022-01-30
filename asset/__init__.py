import os

from .. import global_vars


class DownloadType:
    resolution: int
    format: str

    def ui_name(self):
        return str(self.resolution) + "_" + str(self.format)

    def __init__(self, res, fmt):
        self.resolution = res
        self.format = fmt


class Download:
    dl_format: str
    dl_type: DownloadType
    urls = []

    def __init__(self, fmt, dl_t, _urls):
        self.dl_format = fmt
        self.dl_type = dl_t
        self.urls = _urls


class Asset:
    source: str
    name: str
    fancyName: str
    downloads = []

    def full_name(self):
        return self.source + "_" + self.name

    def preview_path(self):
        return os.path.join(os.path.join(global_vars.cache_dir, "previews"), self.full_name())

    def cache_path(self, dl: DownloadType):
        return os.path.join(os.path.join(os.path.join(global_vars.cache_dir, "downloads"), self.full_name()),
                            dl.ui_name())

    def __init__(self, src, nm, fnm, dls):
        self.source = src
        self.name = nm
        self.fancyName = fnm
        self.downloads = dls


def get_types(material):
    result = [[], []]
    name = material["assetId"]
    if "zip" in material["downloadFolders"]["/"]["downloadFiletypeCategories"]:
        for i in material["downloadFolders"]["/"]["downloadFiletypeCategories"]["zip"]["downloads"]:
            cache_path = os.path.join(os.path.join(os.path.join(global_vars.cache_dir, "downloads"), name),
                                      i["attribute"])
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
