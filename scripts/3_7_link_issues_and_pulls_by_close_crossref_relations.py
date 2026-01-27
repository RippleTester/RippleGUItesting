from pathlib import Path

from src.types.bug import Bugs
from src.utils.file_util import FileUtil
from src.utils.path_util import PathUtil
from config import DATA_DIR, APP_NAME_DESKTOP, APP_NAME_VSCODE, APP_NAME_ZETTLR, APP_NAME_GODOT, APP_NAME_JABREF
import sys


if __name__ == "__main__":
    sys.setrecursionlimit(50000)

    github = "github"
    # reponame = APP_NAME_ZETTLR
    # reponame = APP_NAME_GODOT
    reponame = APP_NAME_JABREF

    issue_pull_relation_foldername = 'issue_pull_closed_crossref_relations'
    pull_issue_relation_foldername = 'pull_issue_closed_crossref_relations'

    issues_filename = 'issues'
    pulls_filename = 'pulls'

    issue_pull_relations_filepath = Path(DATA_DIR, reponame, f"{issue_pull_relation_foldername}.json")
    pull_issue_relations_filepath = Path(DATA_DIR, reponame, f"{pull_issue_relation_foldername}.json")

    issues = FileUtil.load_pickle(PathUtil.get_bugs_filepath(reponame, issues_filename))
    pulls = FileUtil.load_pickle(PathUtil.get_bugs_filepath(reponame, pulls_filename))
    print(f"issues: {len(issues)}")
    print(f"pulls: {len(pulls)}")
    issue_pull_relations = FileUtil.load_json(issue_pull_relations_filepath)
    print(f"issue_pull_relations: {len(issue_pull_relations)}")
    issues = Bugs(issues[:100000])
    issue_pull_relations = issue_pull_relations[:100000]
    pull_issue_relations = None
    if pull_issue_relations_filepath.exists():
        pull_issue_relations = FileUtil.load_json(pull_issue_relations_filepath)
    print(f"issue_pull_relations: {len(issue_pull_relations)}")
    issues.link_issues_and_pulls_by_close_crossref_relations(issue_pull_relations, pulls)
    if pull_issue_relations:
        pulls.link_pulls_and_issues_by_crossref_relation(pull_issue_relations, issues)

    for issue in issues:
        print(issue)
    print("************************************************************")
    for pull in pulls:
        print(pull)
    FileUtil.dump_pickle(PathUtil.get_bugs_filepath(reponame, issues_filename), issues)
    FileUtil.dump_pickle(PathUtil.get_bugs_filepath(reponame, pulls_filename), pulls)
