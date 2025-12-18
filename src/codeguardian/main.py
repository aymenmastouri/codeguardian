#!/usr/bin/env python
import sys
import logging
import warnings
from codeguardian.crew import Codeguardian

warnings.filterwarnings("ignore", category=SyntaxWarning, module="pysbd")

# This main file is intended to be a way for you to run your
# crew locally, so refrain from adding unnecessary logic into this file.
# Replace with inputs you want to test with, it will automatically
# interpolate any tasks and agents information


def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )


def run():
    """
    Run the crew.
    """
    setup_logging()
    crew = Codeguardian().crew()
    result = crew.kickoff()
    print(result)


if __name__ == "__main__":
    run()