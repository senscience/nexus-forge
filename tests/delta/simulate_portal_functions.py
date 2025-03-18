import os
import json
import requests
import collections

from typing import Dict, Any, Union
from kgforge.core import KnowledgeGraphForge

NEXUS_ENDPOINT = "http://localhost:8080/v1"  # Make sure to set your Nexus endpoint in the environment variables


class NexusAPI:
    def __init__(self, endpoint: str, token: str = None):
        self.base_url = endpoint
        self.token = token

        self.headers = {
            "mode": "cors",
            "Content-Type": "application/json",
            "Accept": "application/ld+json, application/json",
        }
        if self.token:
            self.headers["Authorization"] = "Bearer " + self.token

    def _request(
        self,
        method: str,
        path: str,
        data: Dict[str, Any] = None,
        keep_raw: bool = False,
    ) -> Union[Dict[str, Any], requests.Response]:
        """
        Helper method to make HTTP requests.

        Args:
            method (str): The HTTP method to use for the request (e.g., 'GET', 'POST').
            path (str): The API endpoint path.
            data (Dict[str, Any], optional): The data to send with the request. Defaults to None.
            use_json (bool, optional): Whether to send the data as JSON. Defaults to True.
            keep_raw (bool, optional): Whether to return the raw response object. Defaults to False.

        Returns:
            Union[Dict[str, Any], requests.Response]: The response from the HTTP request. If `keep_raw` is True,
            returns the raw `requests.Response` object. Otherwise, returns the decoded JSON response as a dictionary.

        Raises:
            requests.exceptions.RequestException: If an error occurs during the HTTP request.
        """
        url = f"{self.base_url}/{path}"
        try:
            response = requests.request(method, url, headers=self.headers, json=data)
            response.raise_for_status()
            if keep_raw:
                return response
            else:
                return self._decode_json_ordered(response.text)

        except requests.exceptions.RequestException:
            return {"error": response.text}

    def create(
        self, object_type: str, data: Dict[str, Any] = None, path: str = None
    ) -> Dict[str, Any]:

        if path:
            path = f"{object_type}/{path}"

        method = (
            "PUT"
            if object_type in ["orgs", "projects"]
            else "POST"
        )

        return self._request(method, path, data)

    def retrieve(self, object_type: str, object_id: str) -> Dict[str, Any]:

        return self._request("GET", f"{object_type}/{object_id}")

    # to make sure the output response dictionary are always ordered like the response's json
    def _decode_json_ordered(self, s: str):
        return json.JSONDecoder(object_pairs_hook=collections.OrderedDict).decode(s)




# Initialize NexusAPI
nexus_api = NexusAPI(endpoint=NEXUS_ENDPOINT)  # Make sure to set your Nexus endpoint and token in the environment variables


def load_from_file(file_path):
    with open(file_path, 'r') as file:
        return json.load(file)

def create_organization(organization_name, description):
    data = {"description": description}
    response = nexus_api.create("orgs", data, path=organization_name)
    if "error" in response:
        raise Exception(response["error"])
    print(f"Organization '{organization_name}' created successfully.")

def create_project(organization_name, project_name, description):
    data = {"description": description}
    response = nexus_api.create("projects", data, path=f"{organization_name}/{project_name}")
    if "error" in response:
        raise Exception(response["error"])
    print(f"Project '{organization_name}/{project_name}' created successfully.")


def create_resource(organization_name, project_name, resource_content):
    response = nexus_api.create("resources", resource_content, path=f"{organization_name}/{project_name}")
    if "error" in response:
        raise Exception(response["error"])
    print(f"Resource created successfully in project '{organization_name}/{project_name}'.")


def create_schemas(organization_name, project_name, shapes):
    for shape_name, shape_content in shapes.items():
        response = nexus_api.create("schemas", shape_content, path=f"{organization_name}/{project_name}/{shape_name}")
        if "error" in response:
            raise Exception(response["error"])
        print(f"Schema '{shape_name}' created successfully in project '{organization_name}/{project_name}'.")


def create_resources_from_files(forge, resources_dir):
    resources = []
    for filename in os.listdir(resources_dir):
        if filename.endswith(".json"):
            file_path = os.path.join(resources_dir, filename)
            resource_content = load_from_file(file_path)
            with open(file_path, 'r') as file:
                resource_content = json.load(file)
                resource = forge.from_json(resource_content)
                resources.append(resource)
    return resources

def load_schemas_from_directory(directory_path):
    schemas = {}
    for filename in os.listdir(directory_path):
        if filename.endswith(".json"):
            file_path = os.path.join(directory_path, filename)
            with open(file_path, 'r') as file:
                schema_content = json.load(file)
                schema_name = os.path.splitext(filename)[0]
                schemas[schema_name] = schema_content
    return schemas


def main():
    organization_name = "tests"
    project_name = "project"
    org_description = "Testing projects"
    project_description = "Integration tests."

    create_organization(organization_name, org_description)
    create_project(organization_name, project_name, project_description)

    cwd = os.getcwd()
    data_path = os.path.join(cwd, "tests/delta/data")

    # context

    context_filepath = os.path.join(data_path, "shacl_context.json")
    sense_context_filepath = os.path.join(data_path, "config/context.json")

    context_content = load_from_file(context_filepath)
    sense_context = load_from_file(sense_context_filepath)

    # schemas

    schemas_directory = os.path.join(data_path, "shapes")
    schemas = load_schemas_from_directory(schemas_directory)
    create_schemas(organization_name, project_name, schemas)

    create_resource(organization_name, project_name, context_content)
    create_resource(organization_name, project_name, sense_context)

    # Initialize a forge object
    config_path = os.path.join(data_path, "config/forge.yml")
    forge = KnowledgeGraphForge(config_path, endpoint=NEXUS_ENDPOINT,
                            bucket=f"{organization_name}/{project_name}")

    # check that context was correctly resolved, and shapes were loaded
    dtypes = forge._model.types(pretty=False)
    assert len(dtypes) > 0

    # data
    resources_path = os.path.join(data_path, "resources")
    resources = create_resources_from_files(organization_name, project_name, resources_path)
    forge.register(resources)

    for resource in resources:
        forge.validate(resource)


if __name__ == "__main__":
    main()