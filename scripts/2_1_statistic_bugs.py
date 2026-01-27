from datetime import datetime
from pathlib import Path

from src.types.bug import Bugs
from src.utils.file_util import FileUtil
from config import DATA_DIR, APP_NAME_FIREFOX, APP_NAME_THUNDERBIRD
from tqdm import tqdm


if __name__ == "__main__":

    reponame = APP_NAME_FIREFOX
    bug_objects = "bugs"
    start_index = 0
    # end_index = 72621
    end_index = 490644
    bugs_filename = f'{bug_objects}_{start_index}_{end_index}.json'
    filter_bugs_filename = f'filter_by_creation_time_{bugs_filename}'
    filepath = Path(DATA_DIR, reponame, filter_bugs_filename)
    bugs = FileUtil.load_pickle(filepath)

    bugs_with_regressions = Bugs()
    for bug in tqdm(bugs):
        if bug.relation.regressions:
            bugs_with_regressions.append(bug)
    print("**************************************************************************************")
    print(f"len(bugs): {len(bugs)}")
    print(f"len(bugs_with_regressions): {len(bugs_with_regressions)}")
    print(f"len(bugs_with_regressions)/len(bugs): {len(bugs_with_regressions)/len(bugs)}")

    bugs_with_commits = []
    for bug in tqdm(bugs):
        if bug.commits:
            bugs_with_commits.append(bug)
    print(f"len(bugs_with_commits): {len(bugs_with_commits)}")
    # print(len(bugs))
    print(f"len(bugs_with_commits)/len(bugs): {len(bugs_with_commits)/len(bugs)}")

    bugs_with_commits_regressions = []
    for bug in tqdm(bugs_with_commits):
        if bug.relation.regressions:
            bugs_with_commits_regressions.append(bug)
    print(f"len(bugs_with_commits_regressions): {len(bugs_with_commits_regressions)}")
    print(f"len(bugs_with_commits_regressions)/len(bugs_with_commits): {len(bugs_with_commits_regressions)/len(bugs_with_commits)}")

    fixed_bugs_with_commits = Bugs()
    status = set()
    resolution = set()
    for bug in tqdm(bugs):
        # print(bug.status)
        status.add(bug.status)
        resolution.add(bug.resolution)
        if bug.resolution == "FIXED" and bug.commits:
            fixed_bugs_with_commits.append(bug)
    print(status)
    print(resolution)
    print(f"len(fixed_bugs_with_commits): {len(fixed_bugs_with_commits)}")

    fixed_bugs_with_commits_regression = Bugs()
    for bug in tqdm(fixed_bugs_with_commits):
        if bug.relation.regressions:
            fixed_bugs_with_commits_regression.append(bug)
    print(f"len(fixed_bugs_with_commits_regression): {len(fixed_bugs_with_commits_regression)}")
    print(f"{len(fixed_bugs_with_commits_regression)/len(fixed_bugs_with_commits)}")

    print("**********************************************************************")
    if reponame == APP_NAME_FIREFOX:
        products = ["Firefox", "Toolkit", "Core", "DevTools", "Firefox Build System", "WebExtensions"]
    else:
        products = ["Thunderbird"]
    for product in products:
        product_bugs = fixed_bugs_with_commits.get_specified_product_bugs(product)
        print(f"{product} fixed bugs with commits: {len(product_bugs)}")
        product_bugs_with_regressions = Bugs()
        for bug in product_bugs:
            if bug.relation.regressions:
                product_bugs_with_regressions.append(bug)
        print(f"{product} fixed bugs with commits and regressions: {len(product_bugs_with_regressions)}")
        print(len(product_bugs_with_regressions)/len(product_bugs))
        print("**********************************************************************")
