import logging
from logging.handlers import RotatingFileHandler
import os

def setup_logging():
    # Genel log dosyası
    log_dir = "logs"
    if not os.path.exists(log_dir):
        os.mkdir(log_dir)

    # Genel log dosyası yapılandırması
    log_file = os.path.join(log_dir, "app.log")
    file_handler = RotatingFileHandler(log_file, maxBytes=10 * 1024 * 1024, backupCount=5)  # 10MB max size, 5 backups
    file_handler.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(formatter)

    # RunPod özel log dosyası yapılandırması
    runpod_log_file = os.path.join(log_dir, "runpod.log")
    runpod_file_handler = RotatingFileHandler(runpod_log_file, maxBytes=10 * 1024 * 1024, backupCount=5)
    runpod_file_handler.setLevel(logging.ERROR)  # Sadece ERROR seviyesindeki loglar
    runpod_file_handler.setFormatter(formatter)

    # PayTR özel log dosyası yapılandırması
    paytr_log_file = os.path.join(log_dir, "paytr.log")
    paytr_file_handler = RotatingFileHandler(paytr_log_file, maxBytes=10 * 1024 * 1024, backupCount=5)
    paytr_file_handler.setLevel(logging.INFO)  # Sadece ERROR seviyesindeki loglar
    paytr_file_handler.setFormatter(formatter)

    # Konsol logları için stream handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.DEBUG)
    console_handler.setFormatter(formatter)

    # Genel loglama için root logger yapılandırması
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)

    # RunPod logları için ayrı logger
    runpod_logger = logging.getLogger("runpod")
    runpod_logger.setLevel(logging.ERROR)  # Sadece ERROR seviyesindeki loglar
    runpod_logger.addHandler(runpod_file_handler)

    # PayTR logları için ayrı logger
    paytr_logger = logging.getLogger("paytr")
    paytr_logger.setLevel(logging.ERROR)  # Sadece ERROR seviyesindeki loglar
    paytr_logger.addHandler(paytr_file_handler)

    logging.info("Logging setup complete.")
