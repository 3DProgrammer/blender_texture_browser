import os


def get_types(material):
    result = [[], []]
    name = material["assetId"]
    if "zip" in material["downloadFolders"]["/"]["downloadFiletypeCategories"]:
        for i in material["downloadFolders"]["/"]["downloadFiletypeCategories"]["zip"]["downloads"]:
            cache_path = os.path.join(os.path.join(os.path.join(os.path.dirname(
                os.path.realpath(__file__)), "cache"
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
