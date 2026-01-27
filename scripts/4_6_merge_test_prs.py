from pathlib import Path

from src.utils.file_util import FileUtil
from config import APP_OWNER_NAME_ZETTLR, APP_NAME_ZETTLR, DATA_DIR, APP_OWNER_NAME_JABREF, APP_NAME_JABREF, \
    APP_NAME_FIREFOX

if __name__ == "__main__":

    # ownername = APP_OWNER_NAME_ZETTLR
    # reponame = APP_NAME_ZETTLR

    # ownername = APP_OWNER_NAME_GODOT
    # reponame = APP_NAME_GODOT

    ownername = APP_OWNER_NAME_JABREF
    reponame = APP_NAME_JABREF

    # reponame = APP_NAME_FIREFOX

    test_pulls_foldername = "test_pulls"

    test_pulls_path = Path(DATA_DIR, reponame, test_pulls_foldername)

    pulls = []

    for pr_dir in sorted(p for p in test_pulls_path.iterdir() if p.is_dir()):
        pull_json_path = pr_dir / "pull.json"
        if not pull_json_path.exists():
            continue

        pull_data = FileUtil.load_pickle(pull_json_path)
        pulls.append(pull_data)

    output_filepath = Path(test_pulls_path, f"{test_pulls_foldername}.json")
    pulls_sorted = sorted(
        pulls,
        key=lambda p: p.extract_number_from_github_url(),
        reverse=True
    )

    FileUtil.dump_pickle(output_filepath, pulls_sorted)

    print(f"Dumped {len(pulls)} pull.json entries to {str(output_filepath)}")

    for pull in pulls_sorted:
        print(pull.id)
        print(pull.extract_number_from_github_url())
