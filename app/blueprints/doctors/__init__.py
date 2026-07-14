from flask import Blueprint

bp = Blueprint('doctors', __name__, template_folder='../../templates/doctors')

from . import routes  # noqa: F401, E402
