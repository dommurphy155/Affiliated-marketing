from utils.shutdown_handler import setup_shutdown_handler

def cleanup():
    # Clean resources here if needed
    print("Cleaning up before exit...")

setup_shutdown_handler(cleanup)
