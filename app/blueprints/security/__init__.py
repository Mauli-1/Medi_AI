from flask import Blueprint

bp = Blueprint('security', __name__, template_folder='../../templates/security')

from . import routes  # noqa: F401, E402
