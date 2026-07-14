from flask import Blueprint

bp = Blueprint('eprescription', __name__, template_folder='../../templates/eprescription')

from . import routes  # noqa: F401, E402
