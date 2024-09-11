import os
import oss2
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Read the necessary credentials from the environment variables
ALIBABA_ACCESS_KEY_ID = os.getenv('ALIBABA_ACCESS_KEY_ID')
ALIBABA_ACCESS_KEY_SECRET = os.getenv('ALIBABA_ACCESS_KEY_SECRET')
OSS_BUCKET_NAME = os.getenv('OSS_BUCKET_NAME')
OSS_ENDPOINT = os.getenv('OSS_ENDPOINT')

def upload_image_to_oss(local_file_path):
    # Create an instance of the OSS bucket
    auth = oss2.Auth(ALIBABA_ACCESS_KEY_ID, ALIBABA_ACCESS_KEY_SECRET)
    bucket = oss2.Bucket(auth, OSS_ENDPOINT, OSS_BUCKET_NAME)

    # Define the target folder and get the filename
    folder_name = 'multimodal_images'
    file_name = os.path.basename(local_file_path)
    oss_file_path = f"{folder_name}/{file_name}"

    # Upload the file to OSS with public-read ACL
    with open(local_file_path, 'rb') as file:
        bucket.put_object(oss_file_path, file, headers={'x-oss-object-acl': 'public-read'})

    # Construct the public URL
    public_url = f"http://{OSS_BUCKET_NAME}.{OSS_ENDPOINT}/{oss_file_path}"

    return public_url

# Example usage (make sure to set the correct paths and credentials):
if __name__ == "__main__":
    local_path = '/root/multimodal/images/input_image_20240906_120427.jpeg'
    
    try:
        public_url = upload_image_to_oss(local_path)
        print(f"Image uploaded successfully. Public URL: {public_url}")
    except Exception as e:
        print(f"An error occurred: {e}")
