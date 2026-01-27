import json
from pathlib import Path

from src.pipelines.placeholder import Placeholder
from src.pipelines.post_processor import PostProcessor
from src.utils.file_util import FileUtil
from config import APP_NAME_ZETTLR, OUTPUT_DIR, APP_NAME_JABREF, APP_NAME_GODOT, APP_NAME_FIREFOX

if __name__ == "__main__":
    reponame = APP_NAME_FIREFOX
    # reponame = APP_NAME_ZETTLR
    # reponame = APP_NAME_GODOT
    # reponame = APP_NAME_JABREF

    output_filepath = Path(OUTPUT_DIR, reponame, "output")
    numeric_folders = sorted(
        (
            p for p in output_filepath.iterdir()
            if p.is_dir() and p.name.isdigit()
        ),
        key=lambda p: int(p.name),
        reverse=True,
    )

    for folder in numeric_folders[0:]:
        print(folder)
        output = PostProcessor.filter_bugs(folder)
        print(json.dumps(output, indent=2))


