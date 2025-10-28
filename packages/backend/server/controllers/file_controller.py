from flask import request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
import os
from werkzeug.utils import secure_filename
from nlp.text_summarization import summarize_text
from models.db import db
from models.chat import Chat
from models.message import Message
from datetime import datetime
from memory.memory_manager import get_memory_manager

memory_manager = get_memory_manager()

# Fix path joining for cross-platform compatibility
UPLOAD_FOLDER = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'uploads'))
ALLOWED_EXTENSIONS = {'txt', 'pdf'}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@jwt_required()
def upload_file():
    try:
        user_id = get_jwt_identity()
        chat_id = request.form.get('chat_id')

        if 'file' not in request.files:
            return jsonify({'message': 'No file part in the request'}), 400

        file = request.files['file']

        if file.filename == '':
            return jsonify({'message': 'No selected file'}), 400

        if not allowed_file(file.filename):
            return jsonify({'message': 'File type not allowed. Only .txt and .pdf are supported.'}), 400

        # Check file size
        file.seek(0, os.SEEK_END)
        file_size = file.tell()
        file.seek(0) # Reset file pointer to the beginning

        if file_size > MAX_FILE_SIZE:
            return jsonify({'message': f'File size exceeds the limit of {MAX_FILE_SIZE / (1024 * 1024)} MB.'}), 400

        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            filepath = os.path.join(UPLOAD_FOLDER, filename)
            file.save(filepath)

            # Read file content for summarization
            file_content = ""
            if filename.endswith('.txt'):
                with open(filepath, 'r', encoding='utf-8') as f:
                    file_content = f.read()
            elif filename.endswith('.pdf'):
                # Placeholder for PDF text extraction
                # In a real application, you'd use a library like PyPDF2 or pdfminer.six
                file_content = f"[Content of PDF file: {filename} - PDF extraction not yet implemented]"

            # Generate summary
            summary = summarize_text(file_content)

            # Store file information and summary in chat messages
            # First, a message indicating file upload
            file_upload_message = Message(
                chat_id=chat_id,
                sender='user',
                content=f"User uploaded file: {filename}",
                sentiment='neutral'
            )
            db.session.add(file_upload_message)

            # Then, a message with the summary from EVA
            summary_message = Message(
                chat_id=chat_id,
                sender='assistant',
                content=f"Here's a summary of {filename}:\n\n{summary}\n\n[Original document available at: {filepath}]",
                sentiment='positive'
            )
            db.session.add(summary_message)
            db.session.commit()

            # Update chat's last message and updated_at
            chat = Chat.query.get(chat_id)
            if chat:
                chat.last_message = summary_message.content
                chat.updated_at = datetime.utcnow()
                db.session.commit()

            return jsonify({
                'message': 'File uploaded and summarized successfully',
                'filename': filename,
                'summary': summary,
                'filepath': filepath
            }), 200
    except Exception as e:
        db.session.rollback()
        print(f"File upload error: {str(e)}")
        return jsonify({'message': 'Server error'}), 500
