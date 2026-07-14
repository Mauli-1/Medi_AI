from flask import Blueprint

bp = Blueprint('barcode', __name__, template_folder='../../templates/barcode')

from . import routes  # noqa: F401, E402
