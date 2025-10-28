from flask import Blueprint
from controllers.chat_controller import (
    get_chats, 
    create_chat, 
    get_chat_by_id, 
    update_chat, 
    delete_chat,
    get_chat_messages,
    handle_chat_message
)
from controllers.message_controller import (
    add_message, 
    get_message_by_id, 
    delete_message
)

chat_bp = Blueprint('chat', __name__)

# Chat routes
chat_bp.route('/', methods=['GET'])(get_chats)
chat_bp.route('/', methods=['POST'])(create_chat)
chat_bp.route('/<int:chat_id>', methods=['GET'])(get_chat_by_id)
chat_bp.route('/<int:chat_id>', methods=['PUT'])(update_chat)
chat_bp.route('/<int:chat_id>', methods=['DELETE'])(delete_chat)
chat_bp.route('/<int:chat_id>/messages', methods=['GET'])(get_chat_messages)
chat_bp.route('/<int:chat_id>/message', methods=['POST'])(handle_chat_message)

# Message routes
chat_bp.route('/message', methods=['POST'])(add_message)
chat_bp.route('/message/<int:message_id>', methods=['GET'])(get_message_by_id)
chat_bp.route('/message/<int:message_id>', methods=['DELETE'])(delete_message)
