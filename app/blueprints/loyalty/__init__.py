from flask import Blueprint

bp = Blueprint('loyalty', __name__, template_folder='../../templates/loyalty')

from . import routes  # noqa: F401, E402
