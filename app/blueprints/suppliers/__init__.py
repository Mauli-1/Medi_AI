from flask import Blueprint

bp = Blueprint('suppliers', __name__, template_folder='../../templates/suppliers')

from . import routes  # noqa: F401, E402
