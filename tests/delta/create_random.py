import requests
import uuid

# Generate a random UUID
uid = str(uuid.uuid4())

# Define the URL
url = f"http://localhost/v1/{uid}"

# Define the headers
headers = {
    "Content-Type": "application/json"
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