import time

from src.utils.gpt_util import GPTUtil
import requests
from io import BytesIO


class FileSearch:
    # https://platform.openai.com/docs/guides/tools-file-search
    # https://platform.openai.com/docs/guides/retrieval
    # @todo
    def __init__(self, file_id=None, vector_store_id=None):
        self.file_id = file_id
        self.vector_store_id = vector_store_id

    @staticmethod
    def create_file(file_path):
        """
        return file.id
        """
        client = GPTUtil.client
        if file_path.startswith("http://") or file_path.startswith("https://"):
            # Download the file content from the URL
            response = requests.get(file_path)
            file_content = BytesIO(response.content)
            file_name = file_path.split("/")[-1]
            file_tuple = (file_name, file_content)
            result = client.files.create(
                file=file_tuple,
                purpose="assistants"
            )
        else:
            # Handle local file path
            with open(file_path, "rb") as file_content:
                result = client.files.create(
                    file=file_content,
                    purpose="assistants"
                )
        print(f"file_id: {result.id}")
        return result.id

    @staticmethod
    def create_vector_store(vector_store_name):
        vector_store = GPTUtil.client.vector_stores.create(
            name=vector_store_name
        )
        print(f"vector_store_id: {vector_store.id}")
        return vector_store.id

    @staticmethod
    def add_file_to_vector_store(file_id, vector_store_id):
        GPTUtil.client.vector_stores.files.create(
            vector_store_id=vector_store_id,
            file_id=file_id
        )
        # print(result)

    @staticmethod
    def check_file_status(vector_store_id):
        """
        Polls the vector store files until all are processed.

        :param vector_store_id: The ID of the vector store to check.
        :return: Dictionary summarizing the status of files.
        """
        while True:
            # Retrieve the list of files in the vector store
            result = GPTUtil.client.vector_stores.files.list(
                vector_store_id=vector_store_id
            )

            # Assuming 'result' is a SyncCursorPage[VectorStoreFile] object
            statuses = [file.status for file in result]
            status_summary = {
                'in_progress': statuses.count('in_progress'),
                'completed': statuses.count('completed'),
                'cancelled': statuses.count('cancelled'),
                'failed': statuses.count('failed')
            }

            # Display the current status summary
            print(f"Current file statuses: {status_summary}")

            # Check if all files are processed
            if status_summary['in_progress'] == 0:
                break

            # Wait before polling again
            time.sleep(10)  # Adjust the sleep duration as needed

        return status_summary