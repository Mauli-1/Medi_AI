from flask import Blueprint

bp = Blueprint('returns', __name__, template_folder='../../templates/returns')

from . import routes  # noqa: F401, E402
