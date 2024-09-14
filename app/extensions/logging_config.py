import logging
from logging.handlers import RotatingFileHandler
import os

def setup_logging():
    # Log dosyası yolu
    log_dir = "logs"
    if not os.path.exists(log_dir):
        os.mkdir(log_dir)

    log_file = os.path.join(log_dir, "app.log")

    # RotatingFileHandler ile log dosyasının döngüsü
    file_handler = RotatingFileHandler(log_file, maxBytes=10 * 1024 * 1024, backupCount=5)  # 10MB max size, 5 backups
    file_handler.setLevel(logging.INFO)

    # Log formatı: Zaman, Log Seviyesi, Mesaj
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(formatter)

    # Konsol logları için stream handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.DEBUG)
    console_handler.setFormatter(formatter)

    # Root logger'ı yapılandır
    logging.getLogger().setLevel(logging.DEBUG)
    logging.getLogger().addHandler(file_handler)
    logging.getLogger().addHandler(console_handler)

    logging.info("Logging setup complete.")
