from flask import Blueprint

bp = Blueprint('business', __name__, template_folder='../../templates/business')

from . import routes  # noqa: F401, E402
