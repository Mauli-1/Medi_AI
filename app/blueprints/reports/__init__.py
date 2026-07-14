from flask import Blueprint

bp = Blueprint('reports', __name__, template_folder='../../templates/reports')

from . import routes  # noqa: F401, E402
