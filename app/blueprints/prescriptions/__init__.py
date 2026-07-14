from flask import Blueprint

bp = Blueprint('prescriptions', __name__, template_folder='../../templates/prescriptions')

from . import routes  # noqa: F401, E402
