from flask import Blueprint

bp = Blueprint('whatsapp', __name__, template_folder='../../templates/whatsapp')

from . import routes  # noqa: F401, E402
