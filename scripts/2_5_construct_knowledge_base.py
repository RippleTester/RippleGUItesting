import os
from pathlib import Path
from tqdm import tqdm
from src.pipelines.placeholder import Placeholder
from src.types.bug import Bugs
from src.utils.file_util import FileUtil
from config import APP_NAME_FIREFOX, OUTPUT_DIR, DATA_DIR, APP_NAME_VSCODE

from datetime import timedelta

from collections import defaultdict
from datetime import datetime
from typing import List, Tuple

def split_bugs_by_nodes(bugs: List, nodes: List[datetime]):
    """
    bugs: list of bug objects/tuples, must have .creation_time or [1] = datetime
    nodes: list of datetime (sorted ascending = oldest -> newest)
    return: dict[(start_time, end_time), list[bugs]]
            - start_time may be None (for -∞)
            - end_time may be None (for +∞)
    """
    nodes_sorted = sorted(nodes)

    # Build intervals from nodes
    intervals: List[Tuple[datetime, datetime]] = []
    intervals.append((None, nodes_sorted[0]))  # before the first node
    for a, b in zip(nodes_sorted, nodes_sorted[1:]):
        intervals.append((a, b))
    intervals.append((nodes_sorted[-1], None))  # after the last node

    # Allocate bugs into intervals
    blocks = defaultdict(list)
    for bug in bugs:
        # support tuple (id, time) or object with .creation_time
        ct = bug[1] if isinstance(bug, (tuple, list)) else bug.creation_time
        for start, end in intervals:
            if (start is None or ct >= start) and (end is None or ct < end):
                blocks[(start, end)].append(bug)
                break

    return blocks


def cluster_by_gap(times: List[datetime], merge_gap_days: int = 20) -> List[List[datetime]]:
    """
    Group a sorted list of datetimes into clusters:
    - If the gap between two adjacent times <= merge_gap_days, they belong to the same cluster.
    - Otherwise, start a new cluster.
    """
    if not times:
        return []
    gap = timedelta(days=merge_gap_days)
    clusters = [[times[0]]]
    for a, b in zip(times, times[1:]):
        if b - a <= gap:
            clusters[-1].append(b)
        else:
            clusters.append([b])
    return clusters


def choose_nodes_by_clusters(times: List[datetime], k_nodes: int = 7, merge_gap_days: int = 20) -> List[datetime]:
    """
    Rules for selecting time nodes:
    - Node 1: the day before the earliest timestamp (truncated to date granularity).
    - Subsequent nodes: the day before the first timestamp of each following cluster.
    - If the number of clusters - 1 < required nodes,
      then insert extra nodes by splitting the cluster with the largest time span.
      (Simple strategy: take midpoint(s) and use 'the day before' as new nodes.)
    """
    times = sorted(times)
    if not times:
        return []

    clusters = cluster_by_gap(times, merge_gap_days=merge_gap_days)

    # Initial candidates:
    # first one is the day before the earliest timestamp;
    # then the day before the first element of each subsequent cluster.
    candidates = [(clusters[0][0] - timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)]
    for c in clusters[1:]:
        d = (c[0] - timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
        if not candidates or d > candidates[-1]:
            candidates.append(d)

    # If we already have enough candidates, take the earliest k_nodes
    if len(candidates) >= k_nodes:
        return candidates[:k_nodes]

    # Otherwise, add nodes by splitting the cluster with the largest span
    # until we reach k_nodes.
    nodes = candidates[:]
    remaining = k_nodes - len(nodes)

    while remaining > 0:
        # Find the cluster with the maximum time span
        spans = [(c[-1] - c[0], idx) for idx, c in enumerate(clusters)]
        spans.sort(reverse=True, key=lambda x: x[0])
        _, idx = spans[0]
        c = clusters[idx]
        if len(c) < 2:
            # Too small to split, mark as processed
            clusters[idx] = [c[0]]
            continue

        # Take a midpoint in the cluster and use "the day before" as a new node
        mid = c[len(c) // 2]
        new_node = (mid - timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
        if not nodes or new_node > nodes[-1]:
            nodes.append(new_node)
            nodes.sort()
            remaining -= 1
        else:
            # Fallback: shift one day earlier to avoid duplicates
            new_node = new_node - timedelta(days=1)
            if new_node not in nodes:
                nodes.append(new_node)
                nodes.sort()
                remaining -= 1
            else:
                break  # avoid infinite loop

    return nodes[:k_nodes]

# Function: evenly split by size (~8MB)
def split_bugs_evenly_by_size(bug_list, approx_bytes=8 * 1024 * 1024):
    chunks = []
    current = []
    current_size = 0

    for bug in bug_list:
        bug_bytes = len(str(bug.to_dict()).encode("utf-8"))
        if current_size + bug_bytes > approx_bytes and current:
            chunks.append(current)
            current = []
            current_size = 0

        current.append(bug)
        current_size += bug_bytes

    if current:
        chunks.append(current)

    return chunks


if __name__ == "__main__":
    """
    The core workflow is that the bugs (sorted by creation_time in descending order)
    file is too large, and converting it into a vector store causes issues.
    Therefore, we need to split it into multiple files, each approximately 8MB (under 10MB).

    By default, we split the bugs based on the timestamps of the test bugs.
    If no test bugs are available, we instead evenly divide them into chunks of roughly 8MB each.

    In all cases, the final output files must:
    1. contain bugs sorted by creation_time in descending order, and
    2. be named according to the latest creation_time contained in each chunk.
    """

    # -------- Repo Config --------
    reponame = APP_NAME_FIREFOX
    bugs_filename = f"bugs_0_490644"
    test_bugs_foldername = "test_bugs"
    test_bugs_filename = "test_bugs"
    knowledge_base_foldername = f"knowledge_base"

    output_directory = Path(DATA_DIR, reponame, knowledge_base_foldername)
    if not output_directory.exists():
        os.makedirs(output_directory)

    # -------- Load test bugs --------
    try:
        test_bugs_path = Path(DATA_DIR, reponame, test_bugs_foldername, f"{test_bugs_filename}.json")
        test_bugs = FileUtil.load_pickle(test_bugs_path)
    except FileNotFoundError:
        test_bugs = None
        pass

    # -------- Load bugs & sort by creation_time (desc) --------
    bugs_path = Path(DATA_DIR, reponame, f"filter_by_creation_time_and_desc_with_scenario_{bugs_filename}.json")
    bugs = FileUtil.load_pickle(bugs_path)

    # Ensure descending sorting
    bugs.bugs.sort(key=lambda x: x.creation_time, reverse=True)

    # -------- CASE 1: test_bugs available → split by timestamps --------
    if test_bugs and len(test_bugs) > 0:
        print("Using test_bugs timestamps to split...")
        test_bugs.sort_by_closed_time(reverse=True)
        closed_time_list = [bug.closed_time for bug in test_bugs]

        nodes = choose_nodes_by_clusters(
            closed_time_list,
            k_nodes=17,
            merge_gap_days=60
        )

        print("Cut-off nodes:")
        for i, n in enumerate(nodes, 1):
            print(f"{i}: {n:%Y-%m-%d %H:%M:%S}")

        bug_blocks = split_bugs_by_nodes(bugs, nodes)

        # Save each block
        for (start, end), bug_block in bug_blocks.items():

            # block is already sorted by creation_time desc globally
            latest_time = bug_block[0].creation_time   # descending → first is latest

            filename = f"{reponame}_{knowledge_base_foldername}_{latest_time:%Y-%m-%d %H:%M:%S}.json"
            out_path = Path(output_directory, filename)

            print(f"Saving block: {filename} | size={len(bug_block)}")

            FileUtil.dump_json(out_path, [b.to_dict() for b in bug_block])

    # -------- CASE 2: no test_bugs → evenly split by file size --------
    else:
        print("No test_bugs found → evenly splitting by ~8MB chunks...")

        chunks = split_bugs_evenly_by_size(bugs)

        for i, chunk in enumerate(chunks, 1):
            latest_time = chunk[0].creation_time  # since sorted desc

            filename = f"{reponame}_{knowledge_base_foldername}_{latest_time:%Y-%m-%d %H:%M:%S}.json"
            out_path = Path(output_directory, filename)

            print(f"Saving chunk {i}/{len(chunks)}: {filename} | size={len(chunk)}")

            FileUtil.dump_json(out_path, [b.to_dict() for b in chunk])
