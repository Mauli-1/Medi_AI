from flask import Blueprint

bp = Blueprint('users', __name__, template_folder='../../templates/users')

from . import routes  # noqa: F401, E402
