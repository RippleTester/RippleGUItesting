from pathlib import Path

from src.utils.crawl_util import CrawlUtil
from src.utils.file_util import FileUtil
from config import APP_NAME_FIREFOX, DATA_DIR

if __name__ == "__main__":
    """
    1. convert all bug_dicts into bugs
    """
    reponame = APP_NAME_FIREFOX

    builds_filename = 'builds.json'
    builds_filepath = Path(DATA_DIR, reponame)

    builds = CrawlUtil.fetch_firefox_builds()

    FileUtil.dump_json(Path(builds_filepath, builds_filename), builds)



