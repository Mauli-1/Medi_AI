from flask import Blueprint

bp = Blueprint('purchase', __name__, template_folder='../../templates/purchase')

from . import routes  # noqa: F401, E402
