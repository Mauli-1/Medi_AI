from flask import Blueprint

bp = Blueprint('patients', __name__, template_folder='../../templates/patients')

from . import routes  # noqa: F401, E402
