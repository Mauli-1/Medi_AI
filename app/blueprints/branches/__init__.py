from flask import Blueprint

bp = Blueprint('branches', __name__, template_folder='../../templates/branches')

from . import routes  # noqa: F401, E402
