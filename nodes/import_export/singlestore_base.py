import os
import logging
import dtlpy as dl
import singlestoredb as s2

logger = logging.getLogger(name="singlestore-connect")


class SingleStoreBase(dl.BaseServiceRunner):
    """
    A class for running a service that interacts with SingleStore.
    """

    def __init__(self):
        """
        Initializes the ServiceRunner with SingleStore credentials.
        """
        self.logger = logger

    def table_to_dataloop(
        self,
        host: str,
        user: str,
        database: str,
        table_name: str,
        dataset_id: str,
    ):
        """
        Fetches data from a SingleStore table and uploads it to a Dataloop dataset.

        :param host: SingleStore host url.
        :param user: SingleStore username.
        :param database: SingleStore database name.
        :param table_name: SingleStore table name.
        :param dataset_id: Dataloop dataset ID.
        :return: List of uploaded PromptItems.
        """

        self.logger.info(
            "Creating table for dataset '{}' and table '{}'.".format(dataset_id, table_name)
        )

        try:
            dataset = dl.datasets.get(dataset_id=dataset_id)
            self.logger.info("Successfully retrieved dataset with ID '%s'.", dataset_id)
        except dl.exceptions.NotFound as e:
            self.logger.error("Failed to get dataset with ID '%s': %s", dataset_id, e)
            raise e

        # Execute query to fetch data
        query = "SELECT * FROM {}".format(table_name)

        db_config = {
            "host": host,
            "port": 3306,
            "user": user,
            "password": os.environ.get("SINGLESTORE_PASSWORD"),
            "database": database,
            "conn_attrs": {
                "program_name": "SingleStore Integration",
                "version": "0.0.6",
                "provider": "Dataloop"
            },
            'results_type': 'dict' 
        }
        with s2.connect(**db_config) as connection:
            with connection.cursor() as cursor:
                cursor.execute(query)
                rows = cursor.fetchall()§

        prompt_items = []
        for row in rows:
            prompt_item = dl.PromptItem(name=str(row["id"]))
            prompt_item.add(
                message={
                    "role": "user",
                    "content": [
                        {"mimetype": dl.PromptType.TEXT, "value": row["prompt"]}
                    ],
                }
            )
            prompt_items.append(prompt_item)

        items = dataset.items.upload(local_path=prompt_items, overwrite=True, return_as_list=True, raise_on_error=True)

        self.logger.info(
            "Successfully uploaded {} items to dataset '{}'.".format(len(items), dataset_id)
        )
        return items

    def update_table(
        self,
        item: dl.Item,
        host: str,
        user: str,
        database: str,
        table_name: str,
    ):
        """
        Updates a SingleStore table with the best response from a Dataloop item.

        :param item: Dataloop item.
        :param host: SingleStore host url.
        :param user: SingleStore username.
        :param database: SingleStore database name.
        :param table_name: SingleStore table name.
        :return: The updated Dataloop item.
        """

        self.logger.info(
            "Updating table '{}' for item with ID '{}'.".format(table_name, item.id)
        )

        prompt_item = dl.PromptItem.from_item(item)
        first_prompt_key = prompt_item.prompts[0].key

        # Find the best response based on annotation attributes
        best_response = None

        for resp in item.annotations.list():
            try:
                is_best = resp.attributes.get("isBest", False)
            except AttributeError:
                is_best = False
            if is_best and resp.metadata["system"].get("promptId") == first_prompt_key:
                best_response = resp.coordinates
                break

        if best_response is None:
            self.logger.error("No best response found for item ID: {}".format(item.id))
            raise ValueError("No best response found for item ID: {}".format(item.id))

        db_config = {
            "host": host,
            "port": 3306,
            "user": user,
            "password": os.environ.get("SINGLESTORE_PASSWORD"),
            "database": database,
            "conn_attrs": {
                "program_name": "SingleStore Integration",
                "version": "0.0.6",
                "provider": "Dataloop"
            }
        }
        with s2.connect(**db_config) as connection:
            with connection.cursor() as cursor:
                update_query = """
                                UPDATE {}
                                SET RESPONSE = %s
                                WHERE id = %s
                                """.format(table_name)
                cursor.execute(
                    update_query, (best_response, int(prompt_item.name[:-5]))
                )
                connection.commit()

        self.logger.info(
            "Successfully updated table '{}' for item with ID '{}'.".format(table_name, item.id)
        )

        return item
