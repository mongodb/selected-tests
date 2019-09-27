"""
Application to serve API of selected-tests service.
"""

from flask import Flask, jsonify

DEFAULT_PORT = 8080

application = Flask(__name__)


@application.route("/health")
def health():
    """
   Get information about whether service is running
   """
    return jsonify({"online": True})


def main():
    """Run the server."""
    return application.run(host="0.0.0.0", port=DEFAULT_PORT)


if __name__ == "__main__":
    main()
