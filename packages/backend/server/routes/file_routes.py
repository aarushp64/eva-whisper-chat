from flask import Blueprint
from controllers.file_controller import upload_file

file_bp = Blueprint('file', __name__)

file_bp.route('/upload', methods=['POST'])(upload_file)
