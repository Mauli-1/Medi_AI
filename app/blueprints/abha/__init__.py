from flask import Blueprint

bp = Blueprint('abha', __name__, template_folder='../../templates/abha')

from . import routes  # noqa: F401, E402
