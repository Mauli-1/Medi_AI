from flask import Blueprint

bp = Blueprint('gst', __name__, template_folder='../../templates/gst')

from . import routes  # noqa: F401, E402
