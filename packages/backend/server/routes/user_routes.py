from flask import Blueprint
from controllers.user_controller import get_user_profile, update_user_profile, update_user_preferences, add_memorized_detail, get_memorized_details, analyze_conversation_history_controller

user_bp = Blueprint('user_bp', __name__)

user_bp.route('/profile', methods=['GET'])(get_user_profile)
user_bp.route('/profile', methods=['PUT'])(update_user_profile)
user_bp.route('/preferences', methods=['PUT'])(update_user_preferences)
user_bp.route('/preferences/analyze', methods=['POST'])(analyze_conversation_history_controller)
user_bp.route('/memory', methods=['POST'])(add_memorized_detail)
user_bp.route('/memory', methods=['GET'])(get_memorized_details)