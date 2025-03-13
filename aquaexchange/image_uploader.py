from azure.storage.blob import BlobServiceClient, generate_blob_sas, BlobSasPermissions
from datetime import datetime, timedelta
import os
import uuid
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Azure Storage Account details
ACCOUNT_URL = os.getenv("AZURE_ACCOUNT_URL")
AZURE_CREDENTIALS = os.getenv("AZURE_SAS_TOKEN")
CONTAINER_NAME = "opensource-product"  # Replace with your container name

# Initialize BlobServiceClient
blob_service_client = BlobServiceClient(
    account_url=ACCOUNT_URL,
    credential=AZURE_CREDENTIALS
)

# Function to upload a file from disk to Azure Blob Storage
def upload_local_file_to_azure(container_name: str, file_path: str) -> str:
    try:
        # Ensure file exists
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File {file_path} not found.")

        # Get container client
        container_client = blob_service_client.get_container_client(container_name)

        # Ensure the container exists, if not create it
        if not container_client.exists():
            container_client.create_container()

        # Generate a unique blob name
        unique_id = str(uuid.uuid4())
        file_name = os.path.basename(file_path)
        blob_name = f"aquaexchange_images/{unique_id}_{file_name}"

        # Upload the file
        blob_client = container_client.get_blob_client(blob_name)
        with open(file_path, "rb") as data:
            blob_client.upload_blob(data, overwrite=True)

        # Return the uploaded blob name (path in Azure)
        return blob_name
    except Exception as e:
        print(f"Failed to upload file: {str(e)}")
        return None

# Function to generate a pre-signed URL (SAS URL)
def generate_sas_url(container_name: str, blob_name: str) -> str:
    try:
        # Generate a SAS token for the blob
        sas_token = generate_blob_sas(
            account_name=ACCOUNT_URL.split("//")[1].split(".")[0],
            account_key=AZURE_CREDENTIALS,
            container_name=container_name,
            blob_name=blob_name,
            permission=BlobSasPermissions(read=True),
            expiry=datetime.utcnow() + timedelta(hours=1)  # 1-hour expiry
        )

        # Construct the SAS URL
        return f"{ACCOUNT_URL}/{container_name}/{blob_name}?{sas_token}"
    except Exception as e:
        print(f"Failed to generate SAS URL: {str(e)}")
        return None
