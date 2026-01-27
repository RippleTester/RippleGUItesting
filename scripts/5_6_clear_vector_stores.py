from src.utils.gpt_util import GPTUtil
from config import APP_NAME_VSCODE, APP_NAME_FIREFOX, APP_NAME_ZETTLR, APP_NAME_JABREF, APP_NAME_GODOT

if __name__ == "__main__":
    # Choose repo
    # reponame = APP_NAME_FIREFOX
    # reponame = APP_NAME_ZETTLR
    # reponame = APP_NAME_JABREF
    reponame = APP_NAME_GODOT

    stores = GPTUtil.load_vector_stores(reponame)

    for vector_store_name, vector_store_id in stores.items():
        print(f"{vector_store_name} | {vector_store_id}")

        files = GPTUtil.client.vector_stores.files.list(vector_store_id=vector_store_id)

        for f in files.data:
            file_id = f.id
            try:
                print(f"Deleting vector store file: {file_id}")

                # Remove file from vector store
                GPTUtil.client.vector_stores.files.delete(
                    vector_store_id=vector_store_id,
                    file_id=file_id
                )

                # Remove the physical uploaded file
                print(f"Deleting uploaded file: {file_id}")
                GPTUtil.client.files.delete(file_id=file_id)

            except Exception as e:
                print(f"Error deleting file {file_id}: {e}")
                continue

        try:
            # Finally delete the vector store itself
            print(f"Deleting vector store: {vector_store_id}")
            GPTUtil.client.vector_stores.delete(vector_store_id)

        except Exception as e:
            print("Error:", e)
            pass

    stores = GPTUtil.delete_vector_store_file(reponame)

