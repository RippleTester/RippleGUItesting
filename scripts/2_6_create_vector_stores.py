import re
from pathlib import Path
from datetime import datetime
from tqdm import tqdm
from src.utils.gpt_util import GPTUtil
from config import APP_NAME_FIREFOX, DATA_DIR, APP_NAME_VSCODE

if __name__ == "__main__":
    reponame = APP_NAME_FIREFOX

    knowledge_base_foldername = "knowledge_base"
    output_filepath = Path(DATA_DIR, reponame, knowledge_base_foldername)

    file_infos = []  # [(filepath, datetime), ...]

    # Step 1: collect all file paths and their datetime
    if output_filepath.exists() and output_filepath.is_dir():
        for filepath in output_filepath.iterdir():
            if filepath.is_file() and filepath.suffix == ".json":
                match = re.search(r"(\d{4}-\d{2}-\d{2}[ _]\d{2}[:\-]\d{2}[:\-]\d{2})", filepath.name)
                if match:
                    file_datetime = datetime.strptime(match.group(1), "%Y-%m-%d %H:%M:%S")
                    file_infos.append((filepath, file_datetime))
                else:
                    print(f"⚠️ No date found in filename: {filepath.name}")
    else:
        print(f"Directory {output_filepath} does not exist.")

    # Sort by datetime ascending (oldest -> newest)
    file_infos.sort(key=lambda x: x[1])

    # # Debug: print all collected file infos
    # for filepath, dt in file_infos:
    #     print(f"Path: {filepath} | Date: {dt}")

    # Step 2: create vector stores
    file_ids = []
    vector_store_names = []
    stores = GPTUtil.load_vector_stores(reponame)
    for filepath, dt in tqdm(file_infos, ascii=True):
        print(f"Path: {filepath} | Date: {dt}")
        file_id = GPTUtil.create_file(str(filepath))
        file_ids.append(file_id)

        vector_store_name = f"{reponame}_{knowledge_base_foldername}_{dt.isoformat()}"
        vector_store_names.append(vector_store_name)
        print(f"Creating vector store {vector_store_name}")
        vector_store_id = GPTUtil.create_vector_store_by_name(vector_store_name)
        for file_id in file_ids:
            GPTUtil.add_file_to_vector_store(vector_store_id, file_id)
        # GPTUtil.create_vector_store([str(filepath)], vector_store_name)
        stores[vector_store_name] = vector_store_id
        GPTUtil.save_vector_stores(stores, reponame)
        print("###############################################################")

