import os
import dropbox
import logging

DROPBOX_TOKEN = os.getenv("DROPBOX_TOKEN")

def upload_to_storage(file_path):
    try:
        dbx = dropbox.Dropbox(DROPBOX_TOKEN)
        file_name = os.path.basename(file_path)
        dropbox_path = f"/bot_uploads/{file_name}"

        with open(file_path, "rb") as f:
            dbx.files_upload(f.read(), dropbox_path, mode=dropbox.files.WriteMode.overwrite)

        logging.info(f"Uploaded {file_name} to Dropbox successfully.")
    except Exception as e:
        logging.error(f"Dropbox upload failed: {e}")
