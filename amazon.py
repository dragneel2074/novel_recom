import json
import hashlib
import requests
from aws_request_signer import AwsRequestSigner

HOST = "webservices.amazon.com"
URI_PATH = "/paapi5/searchitems"
ACCESS_KEY = "AKIAI2ZWF7R5J7D6P4LQ"
SECRET_KEY = "CbK2g67xoP5K+GqUeitV51vH9g7iiXCe5CS6PMdl"  # replace with your secret key
REGION = "us-east-1"

request_payload = {
    "Keywords": "harem litrpg",
    "Resources": [
        "Images.Primary.Large",
        "ItemInfo.Title"
    ],
    "PartnerTag": "dragneelclub-20",
    "PartnerType": "Associates",
    "Marketplace": "www.amazon.com"
}

headers = {
    "host": HOST,
    "content-type": "application/json; charset=UTF-8",
    "x-amz-target": "com.amazon.paapi5.v1.ProductAdvertisingAPIv1.SearchItems",
    "content-encoding": "amz-1.0"
}

# Create a request signer instance.
request_signer = AwsRequestSigner(
    REGION, ACCESS_KEY, SECRET_KEY, "ProductAdvertisingAPI"
)

# Calculate the SHA-256 hash of the payload.
payload_hash = hashlib.sha256(json.dumps(request_payload).encode()).hexdigest()

# Add the authentication headers.
headers.update(
    request_signer.sign_with_headers("POST", f"https://{HOST}{URI_PATH}", headers, payload_hash)
)

# Make the request.
response = requests.post(f"https://{HOST}{URI_PATH}", headers=headers, json=request_payload)

# Handle the response
if response.status_code == 200:
    print("Successfully received response from Product Advertising API.")
    print(response.json())
else:
    print("Failed to receive response from Product Advertising API.")
    print(f"Response status code: {response.status_code}")
    print(f"Response content: {response.content.decode()}")
