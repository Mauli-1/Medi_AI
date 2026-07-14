from flask import Blueprint

bp = Blueprint('inventory', __name__, template_folder='../../templates/inventory')

from . import routes  # noqa: F401, E402
