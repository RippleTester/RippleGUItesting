

class CoChange:
    def __init__(self, file, commits=None):
        self.file = file  # The file object
        self.commits = commits if commits is not None else []  # The reason for co-changes
# The reason for co-changes
        # self.count = len(self.commits)  # How often this file co-changes

    def __repr__(self):
        # Representation for debugging or logging
        return f"CoChange(file={repr(self.file.path)}, commits={repr(self.commits)})"

    def __str__(self):
        # Human-readable string representation
        commit_details = "\n\t\t".join([str(commit.id) for commit in self.commits])
        return (f"CoChange for file: {self.file.path}\n\t"
                f"\n\tCommits num: {len(self.commits)}\n\t"
                f"Commits:\n\t\t{commit_details}")


class CoChanges:
    def __init__(self):
        self.cochanges = []  # List to hold CoChange objects

    def __iter__(self):
        for cochange in self.cochanges:
            yield cochange

    def __getitem__(self, index):
        return self.cochanges[index]

    def __len__(self):
        return len(self.cochanges)

    def append(self, cochange):
        # Your custom append logic here
        self.cochanges.append(cochange)

    def remove(self, cochange):
        self.cochanges.remove(cochange)

    def add_file(self, file):
        for cochange in self.cochanges:
            if cochange.path == file.path:
                cochange.commits.append(file.last_commit)

    def sort_by_commit_num(self, reverse=True):
        self.cochanges.sort(key=lambda cochange: len(cochange.commits), reverse=reverse)




