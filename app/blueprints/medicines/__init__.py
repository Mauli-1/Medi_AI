from flask import Blueprint

bp = Blueprint('medicines', __name__, template_folder='../../templates/medicines')

from . import routes  # noqa: F401, E402
