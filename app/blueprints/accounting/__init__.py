from flask import Blueprint

bp = Blueprint('accounting', __name__, template_folder='../../templates/accounting')

from . import routes  # noqa: F401, E402
