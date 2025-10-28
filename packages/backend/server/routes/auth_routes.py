from flask import Blueprint
from controllers.auth_controller import register, login, get_current_user, request_password_reset, reset_password

auth_bp = Blueprint('auth', __name__)

# @route   POST /api/auth/register
# @desc    Register a new user
# @access  Public
auth_bp.route('/register', methods=['POST'])(register)

# @route   POST /api/auth/login
# @desc    Login user and get token
# @access  Public
auth_bp.route('/login', methods=['POST'])(login)

# @route   GET /api/auth/me
# @desc    Get current user
# @access  Private
auth_bp.route('/me', methods=['GET'])(get_current_user)

# @route   POST /api/auth/request-reset
# @desc    Request a password reset token
# @access  Public
auth_bp.route('/request-reset', methods=['POST'])(request_password_reset)

# @route   POST /api/auth/reset-password
# @desc    Reset user password using a token
# @access  Public
auth_bp.route('/reset-password', methods=['POST'])(reset_password)
