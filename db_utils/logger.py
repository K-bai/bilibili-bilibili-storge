import logging

logger = logging.getLogger("db_logger")
logger.setLevel(logging.DEBUG)
console = logging.StreamHandler()
console.setFormatter(logging.Formatter("[%(levelname)s][%(asctime)s] %(message)s"))
logger.addHandler(console)
log_file = logging.FileHandler("log.txt", encoding='utf-8')
log_file.setFormatter(logging.Formatter("[%(levelname)s][%(asctime)s] %(message)s"))
logger.addHandler(log_file)