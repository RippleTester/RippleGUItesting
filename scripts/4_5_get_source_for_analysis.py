import asyncio
import os
import sys
from pathlib import Path

from src.pipelines.placeholder import Placeholder
from src.types.bug import Bugs, Bug
from src.types.commit import Commits, Commit
from src.types.file import Files
from src.utils.crawl_util import CrawlUtil
from src.utils.file_util import FileUtil
from src.utils.list_util import ListUtil
from tqdm import tqdm
from github import Github, Auth

from config import DATA_DIR, APP_NAME_DESKTOP, GITHUB_PULL_LINK, GITHUB_ISSUE_LINK, SYNC_CRAWL_NUM, APP_NAME_VSCODE, \
    APP_NAME_ZETTLR, APP_OWNER_NAME_GODOT, APP_NAME_GODOT, APP_OWNER_NAME_JABREF, APP_NAME_JABREF, APP_OWNER_NAME_ZETTLR


def merge_files_under_directory(filepath, save_filename):
    filenames = FileUtil.get_file_names_in_directory(Path(filepath, save_filename), 'json')
    filenames = sorted(filenames, key=lambda x: (len(x), x))
    all_file_contents = []
    for filename in tqdm(filenames, ascii=True):
        file_contents = FileUtil.load_json(filename)
        all_file_contents.extend(file_contents)
    FileUtil.dump_json(Path(filepath, f"{save_filename}.json"), all_file_contents)
    return all_file_contents

def crawl_github_commits_urls_for_pull_request(owner_name, repo_name, pull, save_filepath, headers):
    pull_request_num = pull.extract_number_from_github_url()
    pull_link = GITHUB_PULL_LINK.format(owner_name=owner_name, repo_name=repo_name)
    commits_urls_link = pull_link + f'/{pull_request_num}/commits'
    # print(commits_link)
    commits_urls_dicts = asyncio.run(CrawlUtil.crawl_by_async([commits_urls_link], headers))
    # print(commit_dicts)
    FileUtil.dump_json(Path(save_filepath, "test_commits_urls_dicts.json"), commits_urls_dicts)
    return commits_urls_dicts

def crawl_github_commits_by_shas(commit_shas, owner_name, repo_name, save_filepath,
                                 headers, save_filename="merge_commit_dicts"):
    commit_links = CrawlUtil.get_github_commit_urls(owner_name, repo_name, commit_shas)
    commit_dicts = asyncio.run(CrawlUtil.crawl_by_async(commit_links, headers))
    FileUtil.dump_json(Path(save_filepath, f"{save_filename}.json"), commit_dicts)
    return commit_dicts

def crawl_github_commits_for_pull_request(owner_name, repo_name, save_filepath, headers):
    commits_urls = FileUtil.load_json(Path(save_filepath, f"test_commits_urls_dicts.json"))
    commit_shas = CrawlUtil.get_github_commit_shas_from_commits_links(commits_urls)
    commit_links = CrawlUtil.get_github_commit_urls(owner_name, repo_name, commit_shas)
    commit_dicts = asyncio.run(CrawlUtil.crawl_by_async(commit_links, headers))
    # print(commit_dicts)
    FileUtil.dump_json(Path(save_filepath, "test_commit_dicts.json"), commit_dicts)
    return commit_dicts

def convert_commit_dicts_into_commits(commit_dicts, with_file_patch, test_commits_filepath, test_commits_filename):
    commits = Commits.from_dicts(commit_dicts, with_file_patch)
    FileUtil.dump_pickle(Path(test_commits_filepath, f"{test_commits_filename}.json"), commits)
    return commits

def convert_commit_dict_into_commit(commit_dict, with_file_patch, commit_filepath, commit_filename):
    commit = Commit.from_dict(commit_dict, with_file_patch)
    FileUtil.dump_pickle(Path(commit_filepath, f"{commit_filename}.json"), commit)
    return commit

def add_file_into_blame_object(responses, files):
    objects = []
    for index, response in enumerate(responses):
        file = files[index]
        object = response["data"]["repository"]["object"]
        object["filename"] = object.get("filename", file['filename'])
        objects.append(object)
    return objects

def crawl_github_commit_file_contents_by_commit_parent_id(commit_dicts_filename, save_filepath, headers):
    commits = FileUtil.load_json(Path(save_filepath, f"{commit_dicts_filename}.json"))
    commit_file_content_urls = CrawlUtil.get_github_commit_parent_file_content_urls(ownername, reponame, commits)
    commit_file_content_dicts = asyncio.run(CrawlUtil.crawl_by_async(commit_file_content_urls, headers))
    FileUtil.dump_json(Path(save_filepath, "commit_file_content_dicts.json"), commit_file_content_dicts)
    return commit_file_content_dicts

def crawl_github_commit_file_blames_by_commit_parent_id(commit_dicts_filename, save_filepath, headers):
    commits = FileUtil.load_json(Path(save_filepath, f"{commit_dicts_filename}.json"))
    queries, files = CrawlUtil.get_github_commit_parent_file_blame_queries_for_graphql(ownername, reponame, commits)
    commit_file_blame_dicts = asyncio.run(CrawlUtil.crawl_by_async(queries, headers))
    commit_file_blame_dicts = add_file_into_blame_object(commit_file_blame_dicts, files)
    FileUtil.dump_json(Path(save_filepath, "commit_file_blame_dicts.json"), commit_file_blame_dicts)
    return commit_file_blame_dicts

def crawl_github_pulls_by_blame_commits(blame_commits, owner_name, repo_name, save_filepath, headers):
    commit_shas = []
    for blame_commit in blame_commits:
        commit_shas.append(blame_commit.id)
    pull_urls = CrawlUtil.get_github_pull_urls_from_commit_shas(owner_name, repo_name, commit_shas)
    blame_pull_dicts = asyncio.run(CrawlUtil.crawl_by_async(pull_urls, headers))
    FileUtil.dump_json(Path(save_filepath, "blame_pull_dicts.json"), blame_pull_dicts)
    return blame_pull_dicts

def crawl_github_closed_issues_for_pull_request(owner_name, repo_name, pull, save_filepath, headers):
    issue_nums = pull.get_closed_issues_from_pull_desc()
    issue_links = []
    general_issue_link = GITHUB_ISSUE_LINK.format(owner_name=owner_name, repo_name=repo_name)
    for issue_num in issue_nums:
        issue_link = general_issue_link + f'/{issue_num}'
        issue_links.append(issue_link)
        # print(issue_link)
    closed_issue_dicts = asyncio.run(CrawlUtil.crawl_by_async(issue_links, headers))
    FileUtil.dump_json(Path(save_filepath, "closed_issue_dicts.json"), closed_issue_dicts)
    return closed_issue_dicts

def crawl_github_closed_issues_for_pull_requests(owner_name, repo_name, pulls, save_filepath, headers):
    issues_list = []
    for pull in pulls:
        issue_nums = pull.get_closed_issues_from_pull_desc()
        issue_links = []
        general_issue_link = GITHUB_ISSUE_LINK.format(owner_name=owner_name, repo_name=repo_name)
        for issue_num in issue_nums:
            issue_link = general_issue_link + f'/{issue_num}'
            issue_links.append(issue_link)
            # print(issue_link)
        closed_issue_dicts = asyncio.run(CrawlUtil.crawl_by_async(issue_links, headers))
        issues_list.append(closed_issue_dicts)
    FileUtil.dump_json(Path(save_filepath, "blame_issue_dicts_list.json"), issues_list)
    return issues_list

def get_files_from_file_contents(file_contents, test_commits_filepath, files_filename="files"):
    files = Files.from_file_content_dicts(file_contents)
    FileUtil.dump_pickle(Path(test_commits_filepath, f"{files_filename}.json"), files)
    return files

def crawl_commits_from_file_blames(file_blames, filepath,
                                   owner_name, repo_name,
                                   merge_commits=None,
                                   blame_commits_filename="blame_commits"):
    """
    if test_commits is None:
         crawl all commits from file_annotates
    else:
        crawl commits from file_annotates on deleted and modified lines
    """
    save_filepath = Path(filepath, blame_commits_filename)
    # Check if the folder exists
    if not os.path.exists(save_filepath):
        # If it doesn't exist, create it
        os.makedirs(save_filepath)
    if merge_commits:
        all_commit_shas = []
        for merge_commit in merge_commits:
            commit_shas = CrawlUtil.get_github_commit_shas_from_file_blames_with_test_commit(file_blames, merge_commit)
            all_commit_shas.extend(commit_shas)
        commit_shas = list(set(all_commit_shas))
    else:
        commit_shas = CrawlUtil.get_github_commit_shas_from_file_blames(file_blames)
    # print(commit_shas)
    print(f"annotate commit shas: {len(commit_shas)}")
    # print(len(set(commit_shas)))
    commit_urls = CrawlUtil.get_github_commit_urls(owner_name, repo_name, commit_shas)
    # print(len(commit_urls))
    # print(len(set(commit_urls)))
    commit_urls_list = ListUtil.list_of_groups(commit_urls, SYNC_CRAWL_NUM)
    # loop = asyncio.get_event_loop()
    for index, commits_urls in tqdm(enumerate(commit_urls_list), ascii=True):
        responses = asyncio.run(CrawlUtil.crawl_by_async(commits_urls))
        FileUtil.dump_json(Path(save_filepath,
                                f'{blame_commits_filename}_{index}.json'), responses)
    blame_commits = merge_files_under_directory(filepath, blame_commits_filename)
    print(f"blame commits: {len(blame_commits)}")
    return blame_commits

def convert_bug_dicts_into_bugs_and_link_with_commits(bug_dicts_list, blame_commits, test_commits_filepath,
                                                      ownname, reponame,
                                                      bugs_foldername="blame_pulls",
                                                      commits_foldername="blame_commits"):
    all_bugs = Bugs()
    for index, bug_dicts in enumerate(bug_dicts_list):
        # bugs = Bugs.from_github_dicts(bug_dicts, ownname, reponame)
        for bug_dict in bug_dicts:
            bug = all_bugs.get_bug_by_id(bug_dict['html_url'])
            if not bug:
                bug = Bug.from_github_dict(bug_dict)
                all_bugs.append(bug)
            bug.commits.append(blame_commits[index])
            blame_commits[index].bugs.append(bug)

    FileUtil.dump_pickle(Path(test_commits_filepath, f"{bugs_foldername}.json"), all_bugs)
    FileUtil.dump_pickle(Path(test_commits_filepath, f"{commits_foldername}.json"), blame_commits)
    return all_bugs, blame_commits

# def link_bugs_with_commits(bugs, commits, test_commits_filepath, bugs_foldername="blame_pulls",
#                            commits_foldername="blame_commits"):
#     sys.setrecursionlimit(50000)
#     bugs.link_bugs_with_commits()
#     commits.link_github_pulls_with_commits(bugs)
#     # for commit in commits:
#     #     print(commit)
#     #     for bug in commit.bugs:
#     #         print(bug)
#     #     print("########################################")
#     FileUtil.dump_pickle(Path(test_commits_filepath, f"{commits_foldername}.json"), commits)
#     FileUtil.dump_pickle(Path(test_commits_filepath, f"{bugs_foldername}.json"), bugs)

def convert_issue_dicts_list_into_issues_and_link_with_pulls(blame_issue_dicts_list, blame_pulls, save_filepath,
                                                             issues_foldername="blame_issues",
                                                             pulls_foldername="blame_pulls"):
    issues = Bugs()
    for index, issue_dicts in enumerate(blame_issue_dicts_list):
        for issue_dict in issue_dicts:
            issue = Bug.from_github_dict(issue_dict)
            if issue not in blame_pulls[index].closed_issues:
                blame_pulls[index].closed_issues.append(issue)
            if blame_pulls[index] not in issue.closer_pulls:
                issue.closer_pulls.append(blame_pulls[index])
            if issue not in issues:
                issues.append(issue)
    FileUtil.dump_pickle(Path(save_filepath, f"{issues_foldername}.json"), issues)
    FileUtil.dump_pickle(Path(save_filepath, f"{pulls_foldername}.json"), blame_pulls)
    return issues, blame_pulls

def convert_issue_dicts_into_issues_and_link_with_pull(closed_issue_dicts, pull, save_filepath,
                                                        issues_foldername="closed_issues",
                                                        pulls_foldername="pull"):
    issues = Bugs()
    for issue_dict in closed_issue_dicts:
        issue = Bug.from_github_dict(issue_dict)
        if issue not in pull.closed_issues:
            pull.closed_issues.append(issue)
        if pull not in issue.closer_pulls:
            issue.closer_pulls.append(pull)
        if issue not in issues:
            issues.append(issue)

    FileUtil.dump_pickle(Path(save_filepath, f"{issues_foldername}.json"), issues)
    FileUtil.dump_pickle(Path(save_filepath, f"{pulls_foldername}.json"), pull)
    return issues, pull

def update_blame_commits_by_pull_with_closed_issues(blame_commits, blame_pulls, save_filepath,
                                                    blame_commits_foldername="blame_commits"):
    for blame_commit in blame_commits:
        pulls_with_closed_issues = []
        for bug in blame_commit.bugs:
            blame_pull = blame_pulls.get_bug_by_id(bug.id)
            if blame_pull and blame_pull not in pulls_with_closed_issues:
                pulls_with_closed_issues.append(blame_pull)
        blame_commit.bugs = pulls_with_closed_issues
    FileUtil.dump_pickle(Path(save_filepath, f"{blame_commits_foldername}.json"), blame_commits)
    return blame_commits


def get_file_line_last_commit_from_file_blames(files, commits, file_blames, test_commits_filepath,
                                               files_foldername="files"):
    sys.setrecursionlimit(50000)
    files.get_line_last_commit_by_commit_file_blames(file_blames, commits)
    FileUtil.dump_pickle(Path(test_commits_filepath, f"{files_foldername}.json"), files)

def get_test_scenarios_for_merge_commit(merge_commits, files, commits_filepath=None, ans_filename="ranked_scenarios"):
    test_commit_ranked_scenarios_dict = {}
    for merge_commit in merge_commits:
        bug_count_dict, _ = merge_commit.get_impacted_pulls_issues_by_file_patches(files)
        # bug_count_dict.update(temp_bug_count_dict)

        ranked_scenarios = []
        rank = 1
        for bug, count in bug_count_dict.items():
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
             "commit_message": merge_commit.message,
             "push_date": merge_commit.push_date,
             "ranked_scenarios": ranked_scenarios
        }
        test_commit_ranked_scenarios_dict[merge_commit.html_url] = test_commit_bugs_dict.get(merge_commit.html_url,
                                                                                            test_commit_bugs_dict)
    # print(test_commit_bugs_dict)
    FileUtil.dump_json(Path(commits_filepath, f"{ans_filename}.json"),
                       test_commit_ranked_scenarios_dict)


if __name__ == "__main__":
    github = "github"
    github_token = ""

    headers = {
        'Authorization': f'token {github_token}',
    }

    # ownername = APP_OWNER_NAME_ZETTLR
    # reponame = APP_NAME_ZETTLR

    # ownername = APP_OWNER_NAME_GODOT
    # reponame = APP_NAME_GODOT

    ownername = APP_OWNER_NAME_JABREF
    reponame = APP_NAME_JABREF

    auth = Auth.Token(github_token)
    github = Github(auth=auth)
    repo = github.get_repo(f"{ownername}/{reponame}")

    test_pulls_foldername = "test_pulls"

    with_deleted_modified_file_annotates = True

    filepath = Path(DATA_DIR, reponame)
    merged_pulls = FileUtil.load_pickle(Path(filepath, f"test_merged_pulls.json"))
    # selected_merged_pull = Bugs(merged_pulls).get_bug_by_id("https://github.com/JabRef/jabref/pull/14733")
    # merged_pulls = [selected_merged_pull]

    test_pulls = Bugs()

    for pull in merged_pulls[0:]:
    # for test_pull_url in test_pull_urls:

        print(f"{pull.id}***********************************")
        pull_num = pull.extract_number_from_github_url()
        pr = repo.get_pull(pull_num)
        save_filepath = Path(DATA_DIR, reponame, test_pulls_foldername, f"{pull_num}")
        if not os.path.exists(save_filepath):
            os.makedirs(save_filepath)
        print(f"crawl closed issues...")
        closed_issue_dicts = crawl_github_closed_issues_for_pull_request(ownername, reponame, pull, save_filepath, headers)
        # closed_issue_dicts = FileUtil.load_json(Path(save_filepath, f"closed_issue_dicts.json"))
        closed_issues, pull = convert_issue_dicts_into_issues_and_link_with_pull(closed_issue_dicts, pull, save_filepath)
        # print(pull)
        # # for closed_issue in pull.closed_issues:
        # #     print(closed_issue)
        # #     print(type(closed_issue))
        # for closed_issue in closed_issues:
        #     print(closed_issue)
        print(f"crawl merge commits...")
        merge_commit_sha = pr.merge_commit_sha
        merge_commit_dicts = crawl_github_commits_by_shas([merge_commit_sha], ownername, reponame, save_filepath, headers)
        print("convert merge commits into commit objects...")
        # test_commit_dicts = FileUtil.load_json(Path(save_filepath, "test_commit_dicts.json"))
        merge_commits = convert_commit_dicts_into_commits(merge_commit_dicts, True,
                                                         save_filepath, "merge_commits")
        print(f"crawl test commits...")
        crawl_github_commits_urls_for_pull_request(ownername, reponame, pull, save_filepath, headers)
        test_commit_dicts = crawl_github_commits_for_pull_request(ownername, reponame, save_filepath, headers)
        print("convert test commits into commit objects...")
        # test_commit_dicts = FileUtil.load_json(Path(save_filepath, "test_commit_dicts.json"))
        test_commits = convert_commit_dicts_into_commits(test_commit_dicts, True,
                                                         save_filepath, "test_commits")
        if merge_commits:
            print(f"crawl commit file contents by commit parent id...")
            commit_file_content_dicts = crawl_github_commit_file_contents_by_commit_parent_id(
                "merge_commit_dicts", save_filepath, headers)

            print(f"crawl commit file blames by commit parent id...")
            commit_file_blame_dicts = crawl_github_commit_file_blames_by_commit_parent_id(
                "merge_commit_dicts", save_filepath, headers)

            print("get files from file contents...")
            # commit_file_content_dicts = FileUtil.load_json(Path(save_filepath, f"commit_file_content_dicts.json"))
            files = get_files_from_file_contents(commit_file_content_dicts, save_filepath)
            # test_commits = FileUtil.load_pickle(Path(save_filepath, f"test_commits.json"))
            # commit_file_blame_dicts = FileUtil.load_json(Path(save_filepath, f"commit_file_blame_dicts.json"))
            if with_deleted_modified_file_annotates:
                with_deleted_modified_file_annotates = merge_commits
            blame_commits = crawl_commits_from_file_blames(commit_file_blame_dicts, save_filepath,
                                                           ownername, reponame,
                                                           with_deleted_modified_file_annotates)
            # blame_commits = FileUtil.load_json(Path(save_filepath, f"blame_commits.json"))
            print("convert annotate commits into commit objects...")
            blame_commits = convert_commit_dicts_into_commits(blame_commits, False,
                                                                 save_filepath,
                                                                 "blame_commits")
            # blame_commits = FileUtil.load_pickle(Path(save_filepath, f"blame_commits.json"))

            print("crawl pull requests from blame commits...")
            blame_pull_dicts = crawl_github_pulls_by_blame_commits(blame_commits, ownername, reponame, save_filepath, headers)
            #
            # blame_pull_dicts = FileUtil.load_json(Path(save_filepath, f"blame_pull_dicts.json"))
            print("convert blame_pull_dicts into pulls and link pulls with commits...")
            blame_pulls, blame_commits = convert_bug_dicts_into_bugs_and_link_with_commits(blame_pull_dicts, blame_commits,
                                                                            save_filepath, ownername, reponame,
                                                                            bugs_foldername="blame_pulls",
                                                                            commits_foldername="blame_commits")
            # blame_pulls = FileUtil.load_pickle(Path(save_filepath, f"blame_pulls.json"))

            print(f"crawl blame issues...")
            blame_issue_dicts_list = crawl_github_closed_issues_for_pull_requests(ownername, reponame, blame_pulls, save_filepath, headers)
            # blame_issue_dicts_list = FileUtil.load_json(Path(save_filepath, f"blame_issue_dicts_list.json"))
            blame_issues, blame_pulls = convert_issue_dicts_list_into_issues_and_link_with_pulls(blame_issue_dicts_list, blame_pulls, save_filepath)
            blame_commits = update_blame_commits_by_pull_with_closed_issues(blame_commits, blame_pulls, save_filepath)
            # for blame_pull in blame_pulls:
            #     pull_dict = blame_pull.to_dict()
            #     print(json.dumps(pull_dict, indent=2))
                # print(f"{blame_pull} #########################################")
                # for issue in blame_pull.closed_issues:
                #     print(issue)
            print("get file line last commit from file annotates...")
            files = FileUtil.load_pickle(Path(save_filepath, f"files.json"))

            get_file_line_last_commit_from_file_blames(files, blame_commits, commit_file_blame_dicts,
                                                       save_filepath)

            get_test_scenarios_for_merge_commit(merge_commits, files, save_filepath)

            pull.link_pull_with_commits(test_commit_dicts, test_commits)
            pull.link_pull_with_merge_commits(merge_commits)
            FileUtil.dump_pickle(Path(save_filepath, f"pull.json"), pull)
            FileUtil.dump_pickle(Path(save_filepath, f"test_commits.json"), test_commits)
            FileUtil.dump_pickle(Path(save_filepath, f"merge_commits.json"), merge_commits)
            test_pulls.append(pull)

    FileUtil.dump_pickle(Path(filepath, test_pulls_foldername, f"test_pulls.json"), test_pulls)

