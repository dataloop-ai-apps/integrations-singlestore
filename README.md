# SingleStore Integration

This repository provides a service that enables seamless interaction between **SingleStore** and **Dataloop** using **user-password authentification**. The integration is designed to streamline data processing, table updates, and data uploads between SingleStore and Dataloop datasets.

## Features

- **Secure Authentication** with **user-password authentication** for SingleStore access.
- **SQL Query Execution** on SingleStore directly from Dataloop using the integrated service.
- **Dynamic Table Creation and Updates**: Automatically create and update tables based on Dataloop dataset information.
- **Seamless Data Upload**: Upload SingleStore query results directly to Dataloop datasets.

## Prerequisites

To set up the integration, you'll need the following information:

- **host**, which is SingleStore host url
- **user**
- **password**
- **Database and Table Name** in SingleStore with at least the following columns:
  - **`id`**: Auto-generated field.
  - **`prompt`**: The prompt to create in Dataloop.
  - **`response`**: Field to store model responses (auto-populated from the RLHF pipeline).

## Pipeline Nodes

- **Import SingleStore**

  - This node retrieves prompts from a selected SingleStore table and adds them to a specified dataset in Dataloop, creating prompt items accordingly.

- **Export SingleStore**
  - This node takes the response marked as the best and updates the corresponding SingleStore table row with the response, model name and id from Dataloop.

## Acknowledgments

This project uses the following open-source software:

- [PyMySQL](https://github.com/PyMySQL/PyMySQL): A pure Python MySQL client library. Licensed under the [MIT License](https://opensource.org/licenses/MIT).
