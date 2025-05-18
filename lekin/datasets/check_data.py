"""Check the input job shop format and necessary information"""

import logging


def check_data(data):
    if data.keys() != ["routes", "machines"]:
        logging.error("key")

    if len(data["machines"]) < 1:
        logging.error("machine")
    if len(data["routes"]) < 1:
        logging.error("route")

    return
