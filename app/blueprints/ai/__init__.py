from flask import Blueprint

bp = Blueprint('ai', __name__, template_folder='../../templates/ai')

from . import routes  # noqa: F401, E402
