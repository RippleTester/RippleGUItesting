import asyncio
import os
import sys
from pathlib import Path

from src.pipelines.placeholder import Placeholder
from src.types.bug import Bugs
from src.types.commit import Commits
from src.types.file import Files
from src.utils.crawl_util import CrawlUtil
from src.utils.file_util import FileUtil
from src.utils.list_util import ListUtil
from src.utils.path_util import PathUtil
from config import APP_NAME_FIREFOX, DATA_DIR, SYNC_CRAWL_NUM
from tqdm import tqdm


def merge_files_under_directory(filepath, save_filename):
    filenames = FileUtil.get_file_names_in_directory(Path(filepath, save_filename), 'json')
    filenames = sorted(filenames, key=lambda x: (len(x), x))
    all_file_contents = []
    for filename in tqdm(filenames, ascii=True):
        file_contents = FileUtil.load_json(filename)
        all_file_contents.extend(file_contents)
    FileUtil.dump_json(Path(filepath, f"{save_filename}.json"), all_file_contents)
    return all_file_contents

def crawl_test_commits_for_bug(bug, test_commits_filepath, test_commits_filename="test_commit_dicts"):
    # Check if the folder exists
    if not os.path.exists(test_commits_filepath):
        # If it doesn't exist, create itv
        os.makedirs(test_commits_filepath)
    commit_message_urls = bug.get_hg_commit_json_url_list()
    # loop = asyncio.get_event_loop()
    commit_dicts = asyncio.run(CrawlUtil.crawl_by_async(commit_message_urls))
    FileUtil.dump_json(Path(test_commits_filepath, f'{test_commits_filename}.json'), commit_dicts)
    return commit_dicts


def convert_commit_dicts_into_commits(commit_dicts, with_file_patch, test_commits_filepath, test_commits_filename):
    commits = Commits.from_hg_dicts(commit_dicts, with_file_patch)
    FileUtil.dump_pickle(Path(test_commits_filepath, f"{test_commits_filename}.json"), commits)
    return commits

def get_files_from_file_contents(file_contents, test_commits_filepath, files_filename="files"):
    files = Files.from_hg_file_content_dicts(file_contents)
    FileUtil.dump_pickle(Path(test_commits_filepath, f"{files_filename}.json"), files)
    return files

def crawl_file_contents_by_commit_parent_id(commits, test_commits_filepath,
                                            test_commit_contents_filename="file_contents"):
    file_content_url_list = []
    for commit in commits:
        file_content_urls = commit.get_hg_commit_parent_file_content_urls()
        file_content_url_list.extend(file_content_urls)
    # loop = asyncio.get_event_loop()
    # print(f"file_content_url_list num: {len(file_content_url_list)}")
    # print(f"file_content_url_list")
    file_contents = asyncio.run(CrawlUtil.crawl_by_async(file_content_url_list))
    # file_num = index + 1356
    FileUtil.dump_json(Path(test_commits_filepath,
                            f'{test_commit_contents_filename}.json'), file_contents)
    return file_contents

def crawl_file_blames_by_commit_parent_id(commits, test_commits_filepath,
                                          test_commit_annotates_filename="file_annotates"):
    """
        crawl file blame by commit.parent commit id
    """
    file_annotate_url_list = []
    for commit in commits:
        file_annotate_urls = commit.get_hg_commit_parent_file_annotate_urls()
        file_annotate_url_list.extend(file_annotate_urls)

    file_annotates = asyncio.run(CrawlUtil.crawl_by_async(file_annotate_url_list))
    # file_num = index + 1356
    FileUtil.dump_json(Path(test_commits_filepath,
                            f'{test_commit_annotates_filename}.json'), file_annotates)
    return file_annotates

def crawl_commits_from_file_annotates(file_annotates, test_commits_filepath, test_commits=None,
                                      annotate_commits_filename="annotate_commits"):
    """
    if test_commits is None:
         crawl all commits from file_annotates
    else:
        crawl commits from file_annotates on deleted and modified lines
    """
    save_filepath = Path(test_commits_filepath, annotate_commits_filename)
    # Check if the folder exists
    if not os.path.exists(save_filepath):
        # If it doesn't exist, create it
        os.makedirs(save_filepath)
    if test_commits:
        all_commit_shas = []
        for test_commit in test_commits:
            commit_shas = CrawlUtil.get_hg_commit_shas_from_file_annotates_with_test_commit(file_annotates,
                                                                                            test_commit)
            all_commit_shas.extend(commit_shas)
        commit_shas = list(set(all_commit_shas))
    else:
        commit_shas = CrawlUtil.get_hg_commit_shas_from_file_annotates(file_annotates)
    # print(commit_shas)
    print(f"annotate commit shas: {len(commit_shas)}")
    # print(len(set(commit_shas)))
    commit_urls = CrawlUtil.get_hg_commit_urls(commit_shas)
    # print(len(commit_urls))
    # print(len(set(commit_urls)))
    commit_urls_list = ListUtil.list_of_groups(commit_urls, SYNC_CRAWL_NUM)
    # loop = asyncio.get_event_loop()
    for index, commits_urls in tqdm(enumerate(commit_urls_list), ascii=True):
        responses = asyncio.run(CrawlUtil.crawl_by_async(commits_urls))
        FileUtil.dump_json(Path(save_filepath,
                                f'{annotate_commits_filename}_{index}.json'), responses)
    annotate_commits = merge_files_under_directory(test_commits_filepath, annotate_commits_filename)
    print(f"annotate commits: {len(annotate_commits)}")
    return annotate_commits

def crawl_bug_reports_by_async(bug_ids, test_commits_filepath, bugs_foldername="annotate_bugs",
                               api_key="aIE0knIYYAuzff5sOiD6PGT4mZZZOEg1NF9G0USu"):
    params = {"api_key": api_key}
    save_filepath = Path(test_commits_filepath, bugs_foldername)
    # Check if the folder exists
    if not os.path.exists(save_filepath):
        # If it doesn't exist, create it
        os.makedirs(save_filepath)
    bug_report_urls = CrawlUtil.get_bug_report_urls(bug_ids)
    bug_comments_urls = CrawlUtil.get_bug_comments_urls(bug_ids)
    bug_history_urls = CrawlUtil.get_bug_history_urls(bug_ids)
    bug_attachments_urls = CrawlUtil.get_bug_attachments_urls(bug_ids)

    bug_report_urls_list = ListUtil.list_of_groups(bug_report_urls, SYNC_CRAWL_NUM)
    bug_comments_urls_list = ListUtil.list_of_groups(bug_comments_urls, SYNC_CRAWL_NUM)
    bug_history_urls_list = ListUtil.list_of_groups(bug_history_urls, SYNC_CRAWL_NUM)
    bug_attachments_urls_list = ListUtil.list_of_groups(bug_attachments_urls, SYNC_CRAWL_NUM)

    # loop = asyncio.get_event_loop()

    for index, bug_report_urls in tqdm(enumerate(bug_report_urls_list), ascii=True):
        bug_dicts = []
        bug_responses = asyncio.run(CrawlUtil.crawl_by_async(bug_report_urls, params))
        bug_comments_responses = asyncio.run(
            CrawlUtil.crawl_by_async(bug_comments_urls_list[index], params))
        bug_history_responses = asyncio.run(
            CrawlUtil.crawl_by_async(bug_history_urls_list[index], params))
        bug_attachments_responses = asyncio.run(
            CrawlUtil.crawl_by_async(bug_attachments_urls_list[index], params))

        for bug_response in bug_responses:
            # print(bug_response)
            try:
                bug_dict = bug_response["bugs"][0]
                for bug_comments_response in bug_comments_responses:
                    # print(bug_comments_response)
                    bug_comments_dict = bug_comments_response["bugs"]
                    if str(bug_dict['id']) in bug_comments_dict.keys():
                        # print(bug['id'])
                        bug_dict["comments"] = bug_comments_dict[str(bug_dict['id'])]["comments"]
                        # print(bug["comments"])
                        break
                for bug_history_response in bug_history_responses:
                    bug_history_dict = bug_history_response["bugs"]
                    if bug_history_dict[0]['id'] == bug_dict['id']:
                        # print(bug_history_dict[0]['history'])
                        bug_dict["history"] = bug_history_dict[0]['history']
                        break
                for bug_attachments_response in bug_attachments_responses:
                    # print(bug_attachments_response)
                    bug_attachments_dict = bug_attachments_response["bugs"]
                    if str(bug_dict['id']) in bug_attachments_dict.keys():
                        # print(bug['id'])
                        for bug_attachment in bug_attachments_dict[str(bug_dict['id'])]:
                            bug_attachment['data'] = None
                        bug_dict["attachments"] = bug_attachments_dict[str(bug_dict['id'])]
                        break

                bug_dicts.append(bug_dict)
            except:
                continue
        FileUtil.dump_json(Path(save_filepath, f'{bugs_foldername}_{index}.json'),
                           bug_dicts)
    annotate_bugs = merge_files_under_directory(test_commits_filepath, bugs_foldername)
    return annotate_bugs

def convert_bug_dicts_into_bugs(bug_dicts, test_commits_filepath, bugs_foldername="annotate_bugs"):
    bugs = Bugs.from_dicts(bug_dicts)
    FileUtil.dump_pickle(Path(test_commits_filepath, f"{bugs_foldername}.json"), bugs)
    return bugs

def link_bugs_with_commits(bugs, commits, test_commits_filepath, bugs_foldername="annotate_bugs",
                           commits_foldername="annotate_commits"):
    sys.setrecursionlimit(50000)
    commits.link_hg_bugs_with_commits(bugs)
    # for commit in commits:
    #     print(commit)
    #     for bug in commit.bugs:
    #         print(bug)
    #     print("########################################")
    FileUtil.dump_pickle(Path(test_commits_filepath, f"{commits_foldername}.json"), commits)
    FileUtil.dump_pickle(Path(test_commits_filepath, f"{bugs_foldername}.json"), bugs)

def get_file_line_last_commit_from_file_annotates(files, commits, file_annotates, test_commits_filepath,
                                              files_foldername="files"):
    sys.setrecursionlimit(50000)
    files.get_hg_line_last_commit_by_file_annotates(file_annotates, commits)
    FileUtil.dump_pickle(Path(test_commits_filepath, f"{files_foldername}.json"), files)

def get_test_scenarios_for_test_commit(test_commits, files, test_commits_filepath=None, ans_filename="ranked_scenarios"):
    test_commit_ranked_scenarios_dict = {}
    for test_commit in test_commits:
        bug_count_dict, _ = test_commit.get_impacted_pulls_issues_by_file_patches(files)
        # bug_count_dict.update(temp_bug_count_dict)

        ranked_scenarios = []
        rank = 1
        for bug, count in bug_count_dict.items():
            # @todo
            bug_dict = bug.to_dict()
            # test_scenarios = bug.get_test_scenarios()
            # if bug:
                # test_scenarios = json.loads(test_scenarios)
            bug_dict[Placeholder.RANK] = bug_dict.get(Placeholder.RANK, rank)
            bug_dict[Placeholder.COUNT] = bug_dict.get(Placeholder.COUNT, count)
            rank = rank + 1
                # scenario = {"rank": index, "bug_url": f"{MOZILLA_BUG_LINK}{bug.id}",
                #             "bug_summary": bug.summary, "bug_desc": bug.description.text, "count": count}
            ranked_scenarios.append(bug_dict)
        test_commit_bugs_dict = {
            # "commit_url": test_commit.html_url,
             "commit_message": test_commit.message,
             "push_date": test_commit.push_date,
             "ranked_scenarios": ranked_scenarios
        }
        test_commit_ranked_scenarios_dict[test_commit.html_url] = test_commit_bugs_dict.get(test_commit.html_url,
                                                                                            test_commit_bugs_dict)
    # print(test_commit_bugs_dict)
    FileUtil.dump_json(Path(test_commits_filepath, f"{ans_filename}.json"),
                       test_commit_ranked_scenarios_dict)


if __name__ == "__main__":
    reponame = APP_NAME_FIREFOX
    test_bugs_foldername = "test_bugs"
    bugs_filename = 'test_bugs'
    with_deleted_modified_file_annotates = True

    bugs = FileUtil.load_pickle(PathUtil.get_bugs_filepath(Path(reponame, test_bugs_foldername), f"{bugs_filename}"))
    for bug in tqdm(bugs, ascii=True):
        """
        crawl bug.commits
        """
        # if bug.id in bug_ids:
        #     continue
        test_commits_filepath = Path(DATA_DIR, reponame, test_bugs_foldername, f"{bug.id}")

        # Check if the folder exists
        if not os.path.exists(test_commits_filepath):
            # If it doesn't exist, create itv
            os.makedirs(test_commits_filepath)
        print(f"crawl test commits for bug {bug.id}...")
        commit_dicts = crawl_test_commits_for_bug(bug, test_commits_filepath)
        # print(f"OK")
        # print(commit_dicts[0])
        print("convert test commits into commit objects...")
        test_commits = convert_commit_dicts_into_commits(commit_dicts, True, test_commits_filepath,
                                                                 "test_commits")
        # print(test_commits[0])
        if test_commits:
            print("crawl file contents by commit parent id...")
            file_contents = crawl_file_contents_by_commit_parent_id(test_commits, test_commits_filepath)
            print("crawl file annotates by commit parent id...")
            file_annotates = crawl_file_blames_by_commit_parent_id(test_commits, test_commits_filepath)
            print("get files from file contents...")
            files = get_files_from_file_contents(file_contents, test_commits_filepath)
            print("crawl annotate commits from file annotates...")
            # print(len(file_annotates))
            if with_deleted_modified_file_annotates:
                with_deleted_modified_file_annotates = test_commits
            annotate_commits = crawl_commits_from_file_annotates(file_annotates, test_commits_filepath,
                                                                 with_deleted_modified_file_annotates)
            print("convert annotate commits into commit objects...")
            annotate_commits = convert_commit_dicts_into_commits(annotate_commits, False,
                                                                 test_commits_filepath,
                                                                 "annotate_commits")
            # print(f"annotate commits: {len(annotate_commits)}")
            print("crawl bug reports from annotate commits...")
            bug_ids = annotate_commits.get_bug_ids_from_message()
            bug_dicts = crawl_bug_reports_by_async(bug_ids, test_commits_filepath)
            print("convert bug reports into bugs...")
            annotate_bugs = convert_bug_dicts_into_bugs(bug_dicts, test_commits_filepath)
            print("link annotate bugs with annotate commits ...")
            link_bugs_with_commits(annotate_bugs, annotate_commits, test_commits_filepath)

            # print("get file line last commit from file annotates...")
            get_file_line_last_commit_from_file_annotates(files, annotate_commits, file_annotates,
                                                          test_commits_filepath)

            get_test_scenarios_for_test_commit(test_commits, files, test_commits_filepath)

