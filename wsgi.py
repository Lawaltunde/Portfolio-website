import logging
import sys
import os

# Redirect stdout and stderr to the logging module
class StreamToLogger:
    """
    Fake file-like stream object that redirects writes to a logger instance.
    """
    def __init__(self, logger, log_level=logging.INFO):
        self.logger = logger
        self.log_level = log_level
        self.linebuf = ''

    def write(self, buf):
        for line in buf.rstrip().splitlines():
            self.logger.log(self.log_level, line.rstrip())

    def flush(self):
        pass

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

sys.stdout = StreamToLogger(logger, logging.INFO)
sys.stderr = StreamToLogger(logger, logging.ERROR)


logger.info("WSGI script started.")
try:
    # Add the project's root directory to the Python path to ensure imports work correctly
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__))))

    from portfolio.app import create_app

    # Create the Flask app
    logger.info("Successfully imported create_app.")
    app = create_app()
    logger.info("Successfully created app.")
except Exception as e:
    logger.error(f"Error in wsgi.py: {e}", exc_info=True)
    # It's important to raise the exception so the server knows something went wrong.
    raise