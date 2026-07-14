from flask import Blueprint

bp = Blueprint('compliance', __name__, template_folder='../../templates/compliance')

from . import routes  # noqa: F401, E402
