import os, logging

def clean_temp(folder="temp"):
    try:
        for f in os.listdir(folder):
            os.remove(os.path.join(folder, f))
        logging.info(f"Temp folder '{folder}' cleaned.")
    except Exception as e:
        logging.warning(f"Failed to clean temp: {e}")
