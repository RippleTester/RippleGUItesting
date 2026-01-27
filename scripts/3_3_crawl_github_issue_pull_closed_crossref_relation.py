import asyncio
import os
from pathlib import Path

from tqdm import tqdm

from src.utils.crawl_util import CrawlUtil
from src.utils.file_util import FileUtil
from src.utils.list_util import ListUtil
from config import DATA_DIR, SYNC_CRAWL_NUM, GITHUB_GRAPHQL_LINK, APP_NAME_DESKTOP, APP_NAME_VSCODE, APP_NAME_ZETTLR, \
    APP_NAME_GODOT, APP_OWNER_NAME_GODOT, APP_OWNER_NAME_JABREF, APP_NAME_JABREF

if __name__ == "__main__":
    github = "github"

    # ownername = "Zettlr"
    # reponame = APP_NAME_ZETTLR

    # ownername = APP_OWNER_NAME_GODOT
    # reponame = APP_NAME_GODOT

    ownername = APP_OWNER_NAME_JABREF
    reponame = APP_NAME_JABREF

    foldername = 'issue_dicts'
    save_foldername = 'issue_pull_closed_crossref_relations'

    github_token = ""

    headers = {
        'Authorization': f'token {github_token}',
    }
    url = GITHUB_GRAPHQL_LINK

    filepath = Path(DATA_DIR, reponame)
    save_filepath = Path(filepath, f'{save_foldername}')
    # Check if the folder exists
    if not os.path.exists(save_filepath):
        # If it doesn't exist, create it
        os.makedirs(save_filepath)

    issues = FileUtil.load_json(Path(filepath, f"{foldername}.json"))
    print(len(issues))
    # commits = FileUtil.load_json(Path(DATA_DIR, 'github', reponame, 'commits', f'commits_urls_0.json'))
    issue_nums = CrawlUtil.get_github_issue_or_pull_request_nums(issues)
    print(len(issue_nums))
    # queries = CrawlUtil.get_github_issue_pull_request_closed_relation_queries_for_graphql(ownername, reponame, issue_nums)
    queries = CrawlUtil.get_github_issue_pull_close_crossref_relation_queries_for_graphql(ownername, reponame, issue_nums)

    corresponding_pulls = []
    queries_list = ListUtil.list_of_groups(queries, SYNC_CRAWL_NUM)
    # loop = asyncio.get_event_loop()
    for index, queries in tqdm(enumerate(queries_list), ascii=True):
        responses = asyncio.run(CrawlUtil.crawl_by_async(queries, headers))
        FileUtil.dump_json(Path(save_filepath,
                                f'{save_foldername}_{index}.json'), responses)
