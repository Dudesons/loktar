import connexion
import logging
import sys

app = connexion.App(__name__, debug=True, specification_dir='storage_proxy/')

for hdlr in app.app.logger.handlers:  # remove all old handlers
    app.app.logger.removeHandler(hdlr)

# Set handler
handler = logging.StreamHandler()
log_formatter = logging.Formatter("[%(levelname)s] [(filename)s] [%(asctime)s] %(message)s")
handler.setFormatter(log_formatter)
handler.setLevel(logging.DEBUG)
# handler.setLevel(logging.INFO)
app.app.logger.addHandler(handler)
app.app.logger.setLevel(logging.DEBUG)
# app.app.logger.setLevel(logging.INFO)

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)
# logger.setLevel(logging.INFO)
handler.setFormatter(log_formatter)
logger.addHandler(handler)


@app.app.errorhandler(Exception)
def handle_invalid_usage(error):
    """Handle uncatched error.

    Log the error and retrun a 500.
    Args:
        error: the exception raised by the microservice.
    """

    app.app.logger.error(str(error))
    return 'Internal Error', 500

app.add_api('swagger.yaml')

if __name__ == '__main__':
    # Get port from command line
    app.port = int(sys.argv[1]) if len(sys.argv) > 1 else 8080
    app.run()
