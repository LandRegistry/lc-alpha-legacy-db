import logging
import json


def record_error(details):
    # In beta this will write to the legacy error logging mechanism
    # Here, just write to the log file...
    logging.error(json.dumps(details))
