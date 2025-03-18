import requests
import uuid

# Define the URL
url = f"http://localhost:8080/v1/orgs/random_{uuid.uuid4()}"

# Define the headers

headers = {
            "mode": "cors",
            "Content-Type": "application/json",
            "Accept": "application/ld+json, application/json",
}

# Define the data
data = {
    "description": "random organization"
}

# Make the PUT request
response = requests.put(url, json=data, headers=headers)

# Print the response
print(response.status_code)
print(response.json())
response.raise_for_status()