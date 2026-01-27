import asyncio
import os
from pathlib import Path
from tqdm import tqdm
from src.utils.crawl_util import CrawlUtil
from src.utils.file_util import FileUtil
from src.utils.list_util import ListUtil
from config import SYNC_CRAWL_NUM, DATA_DIR, APP_OWNER_NAME_GODOT, APP_NAME_GODOT, APP_NAME_JABREF, \
    APP_OWNER_NAME_JABREF, APP_OWNER_NAME_ZETTLR, APP_NAME_ZETTLR

if __name__ == "__main__":
    github_token = ""

    headers = {
        'Authorization': f'token {github_token}',
    }
    # headers = None

    folder_name = "test_issues_pulls"

    index_offset = 0
    # GitHub repository information
    # owner = APP_OWNER_NAME_ZETTLR
    # repo = APP_NAME_ZETTLR
    # owner = APP_OWNER_NAME_GODOT
    # repo = APP_NAME_GODOT
    owner = APP_OWNER_NAME_JABREF
    repo = APP_NAME_JABREF
    # max_issue_id = 272277
    max_issue_id = 14456
    min_issue_id = 14320

    filepath = Path(DATA_DIR, repo, folder_name)

    # Check if the folder exists
    if not os.path.exists(filepath):
        # If it doesn't exist, create it
        os.makedirs(filepath)

    issue_urls = CrawlUtil.get_github_issue_urls(owner, repo, max_issue_id=max_issue_id, min_issue_id=min_issue_id)

    issue_urls_list = ListUtil.list_of_groups(issue_urls, SYNC_CRAWL_NUM)
    # loop = asyncio.get_event_loop()
    for index, issue_urls in tqdm(enumerate(issue_urls_list), ascii=True):
        # print(f"{issue_urls[0]}")
        responses = asyncio.run(CrawlUtil.crawl_by_async(issue_urls, headers))
        FileUtil.dump_json(Path(filepath, f'{folder_name}_{index+index_offset}.json'), responses)
