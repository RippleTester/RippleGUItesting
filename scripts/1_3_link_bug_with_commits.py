from pathlib import Path

from src.utils.file_util import FileUtil
from src.utils.path_util import PathUtil
from config import APP_NAME_FIREFOX, DATA_DIR
from tqdm import tqdm

if __name__ == "__main__":
    reponame = APP_NAME_FIREFOX
    bugs_foldername = 'test_bugs'
    bugs_filename = 'test_bugs'
    bugs = FileUtil.load_pickle(PathUtil.get_bugs_filepath(Path(reponame, bugs_foldername), f"{bugs_filename}"))

    for bug in tqdm(bugs, ascii=True):
        """
        crawl bug.commits
        """
        test_commits_filepath = Path(DATA_DIR, reponame, bugs_foldername, f"{bug.id}", "test_commits.json")
        test_commits = FileUtil.load_pickle(test_commits_filepath)
        bug.link_bug_with_commits(test_commits)
        FileUtil.dump_pickle(test_commits_filepath, test_commits)
    FileUtil.dump_pickle(PathUtil.get_bugs_filepath(Path(reponame, bugs_foldername), f"{bugs_filename}"), bugs)

