from cgitb import reset
from os.path import abspath, dirname, join

CURR_DIR=dirname(abspath(__file__))

def get_labels(name, background_label=None):
    if name.lower() in ("coco80", "coco90", "imagenet1000"):
        file_path = join(CURR_DIR, name.lower()+".labels")
        result = [] if background_label is None else [background_label]
        with open(file_path) as ifile:
            for l in ifile: result.append(l.strip())
        return result
    return []

if __name__ == "__main__":
    pass
