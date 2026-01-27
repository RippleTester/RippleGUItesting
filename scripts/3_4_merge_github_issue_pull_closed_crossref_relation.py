from pathlib import Path

from tqdm import tqdm

from src.utils.file_util import FileUtil
from config import DATA_DIR, APP_NAME_DESKTOP, APP_NAME_VSCODE, APP_NAME_ZETTLR, APP_OWNER_NAME_GODOT, APP_NAME_GODOT, \
    APP_OWNER_NAME_JABREF, APP_NAME_JABREF

if __name__ == "__main__":
    github = "github"

    # ownername = "Zettlr"
    # reponame = APP_NAME_ZETTLR

    # ownername = APP_OWNER_NAME_GODOT
    # reponame = APP_NAME_GODOT

    ownername = APP_OWNER_NAME_JABREF
    reponame = APP_NAME_JABREF

    foldername = 'issue_pull_closed_crossref_relations'

    filepath = Path(DATA_DIR, reponame)

    filenames = FileUtil.get_file_names_in_directory(
        Path(filepath, foldername), 'json')
    filenames = sorted(filenames, key=lambda x: (len(x), x))
    all_relations = []
    for filename in tqdm(filenames, ascii=True):
        relations = FileUtil.load_json(filename)
        all_relations.extend(relations)
    print(len(all_relations))
    FileUtil.dump_json(Path(filepath, f"{foldername}.json"), all_relations)
