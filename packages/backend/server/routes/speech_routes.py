from flask import Blueprint
from controllers.speech_controller import process_speech_command

speech_bp = Blueprint('speech', __name__)

speech_bp.route('/command', methods=['POST'])(process_speech_command)
