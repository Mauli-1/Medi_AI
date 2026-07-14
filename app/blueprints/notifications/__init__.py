from flask import Blueprint

bp = Blueprint('notifications', __name__, template_folder='../../templates/notifications')

from . import routes  # noqa: F401, E402
