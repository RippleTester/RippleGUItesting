import asyncio
import logging
import os
from pathlib import Path
from tqdm import tqdm
from src.utils.crawl_util import CrawlUtil
from src.utils.file_util import FileUtil
from src.utils.list_util import ListUtil
from config import DATA_DIR, SYNC_CRAWL_NUM, APP_NAME_FIREFOX, MIN_SLEEP_TIME, APP_NAME_THUNDERBIRD

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")


def prepare_directories(save_foldername, bugs_filename):
    """Ensure directories for saving data exist."""
    path = Path(save_foldername, bugs_filename)
    os.makedirs(path, exist_ok=True)
    return path


def get_bug_ids(file_path, start_index, end_index):
    """Load and preprocess bug IDs."""
    bug_ids = FileUtil.load_txt(file_path)
    bug_ids = [int(x.strip()) for x in bug_ids]
    bug_ids.sort(reverse=True)
    return bug_ids[start_index:end_index]


def process_bug_data(bug_responses, bug_comments_responses, bug_history_responses, bug_attachments_responses):
    """Merge bug responses with comments, history, and attachments."""
    bug_dicts = []
    for bug_response in bug_responses:
        try:
            bug_dict = bug_response["bugs"][0]
            # Attach comments
            for bug_comments_response in bug_comments_responses:
                bug_comments_dict = bug_comments_response["bugs"]
                if str(bug_dict['id']) in bug_comments_dict:
                    bug_dict["comments"] = bug_comments_dict[str(bug_dict['id'])]["comments"]
                    break
            # Attach history
            for bug_history_response in bug_history_responses:
                bug_history_dict = bug_history_response["bugs"]
                if bug_history_dict[0]['id'] == bug_dict['id']:
                    bug_dict["history"] = bug_history_dict[0]['history']
                    break
            # Attach attachments
            for bug_attachments_response in bug_attachments_responses:
                bug_attachments_dict = bug_attachments_response["bugs"]
                if str(bug_dict['id']) in bug_attachments_dict:
                    for attachment in bug_attachments_dict[str(bug_dict['id'])]:
                        attachment['data'] = None
                    bug_dict["attachments"] = bug_attachments_dict[str(bug_dict['id'])]
                    break
            bug_dicts.append(bug_dict)
        except KeyError as e:
            logging.warning(f"KeyError while processing bug data: {e}")
        except Exception as e:
            logging.error(f"Unexpected error: {e}")
    return bug_dicts


async def main():
    # Initialization
    relink_index = 0
    app_name = APP_NAME_FIREFOX

    start_index = 0
    end_index = -1
    test_flag = False
    api_key = "zUsIKhjcfnE4N2zmFvu7dF0tKVmia0sE5vSXqRWx"
    params = {"api_key": api_key}
    bug_dicts_foldername = f"bug_dicts"

    bugs_filename = f"test_bugs_{start_index}_{end_index}" if test_flag else f"bugs_{start_index}_{end_index}"
    bug_ids_filename = "test_bug_ids" if test_flag else "bug_ids"

    save_foldername = Path(DATA_DIR, app_name, bug_dicts_foldername)
    save_path = prepare_directories(save_foldername, bugs_filename)

    # Load and prepare bug IDs
    bug_ids = get_bug_ids(Path(save_foldername, f"{bug_ids_filename}.txt"), start_index, end_index)
    logging.info(f"Loaded {len(bug_ids)} bug IDs from {start_index} to {end_index}")

    # Generate URLs
    bug_report_urls = CrawlUtil.get_bug_report_urls(bug_ids)
    bug_comments_urls = CrawlUtil.get_bug_comments_urls(bug_ids)
    bug_history_urls = CrawlUtil.get_bug_history_urls(bug_ids)
    bug_attachments_urls = CrawlUtil.get_bug_attachments_urls(bug_ids)

    # Group URLs for batched processing
    report_batches = ListUtil.list_of_groups(bug_report_urls, SYNC_CRAWL_NUM)
    comments_batches = ListUtil.list_of_groups(bug_comments_urls, SYNC_CRAWL_NUM)
    history_batches = ListUtil.list_of_groups(bug_history_urls, SYNC_CRAWL_NUM)
    attachments_batches = ListUtil.list_of_groups(bug_attachments_urls, SYNC_CRAWL_NUM)

    # Crawl data in batches
    for index, (report_urls, comments_urls, history_urls, attachments_urls) in tqdm(
            enumerate(zip(report_batches[relink_index:], comments_batches, history_batches, attachments_batches)),
            ascii=True, total=len(report_batches[relink_index:])
    ):
        logging.info(f"Processing batch {index + relink_index + 1}")
        bug_responses = await CrawlUtil.crawl_by_async(report_urls, params)
        bug_comments_responses = await CrawlUtil.crawl_by_async(comments_urls, params)
        bug_history_responses = await CrawlUtil.crawl_by_async(history_urls, params)
        bug_attachments_responses = await CrawlUtil.crawl_by_async(attachments_urls, params)
        # await asyncio.sleep(MIN_SLEEP_TIME)  # 30 seconds
        # Process and save data
        bug_dicts = process_bug_data(bug_responses, bug_comments_responses, bug_history_responses,
                                     bug_attachments_responses)
        FileUtil.dump_json(Path(save_path, f"{bugs_filename}_{index + relink_index}.json"), bug_dicts)


if __name__ == "__main__":
    asyncio.run(main())

