from flask import Blueprint
from controllers.group_controller import (
    create_group,
    invite_user_to_group,
    get_user_groups,
    get_group_members,
    get_group_chat_messages
)

group_bp = Blueprint('group', __name__)

group_bp.route('/', methods=['POST'])(create_group)
group_bp.route('/invite', methods=['POST'])(invite_user_to_group)
group_bp.route('/my-groups', methods=['GET'])(get_user_groups)
group_bp.route('/<int:group_id>/members', methods=['GET'])(get_group_members)
group_bp.route('/<int:group_id>/messages', methods=['GET'])(get_group_chat_messages)
