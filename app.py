from pathlib import Path
import os
import shutil
import gradio as gr
from account import signup, login
from groq import Groq
from book_engine import extract_pdf_text, create_chunks
from conversation import generate_reply
from database import initialize_database, save_memory, load_memories, replace_memory, delete_memory, save_user_knowledge, load_user_knowledge, delete_user_knowledge
from identity import create_session_id, memory_user_id
from memory_extractor import extract_memory
from mind import build_adviser_mind
from mind_cache import file_fingerprint, versioned_fingerprint, load_cached_mind, save_cached_mind
from session import AdviserSession
client = Groq(api_key=os.getenv('GROQ_API_KEY'))
initialize_database()
user_sessions = {}

def get_session(session_id, user_id=None):
    """
    Return an isolated Adviser session for
    this browser session + authenticated user.
    """
    owner = memory_user_id(session_id, authenticated_user_id=user_id)
    session_key = (str(session_id), str(owner))
    if session_key not in user_sessions:
        session = AdviserSession()
        for memory in load_memories(owner):
            session.memory.add(memory)
        user_sessions[session_key] = session
    return user_sessions[session_key]

def reset_upload_file():
    """Clear the file picker after processing."""
    return None

def learn_book(file, session_id, user_id):
    if file is None:
        return ('Choose a PDF first.', gr.update(), knowledge_library_text(user_id), knowledge_removal_choices(user_id))
    session = get_session(session_id, user_id)
    try:
        if isinstance(file, str):
            file_path = file
        else:
            file_path = getattr(file, 'name', str(file))
        pages = extract_pdf_text(file_path)
        if not pages or not any((str(page.get('text', '')).strip() for page in pages)):
            return ("I couldn't find readable text in that PDF.", gr.update(), knowledge_library_text(user_id), knowledge_removal_choices(user_id))
        chunks = create_chunks(pages)
        file_hash = file_fingerprint(file_path)
        fingerprint = versioned_fingerprint(file_hash)
        adviser_mind = load_cached_mind(fingerprint)
        if not adviser_mind:
            adviser_mind = build_adviser_mind(client, pages)
            save_cached_mind(fingerprint, adviser_mind)
        if not user_id:
            raise ValueError('Authentication required.')
        save_user_knowledge(user_id, file_hash, Path(file_path).name, adviser_mind, chunks)
        records = load_user_knowledge(user_id)
        all_chunks = []
        all_minds = []
        for record in records:
            saved_chunks = record.get('chunks', [])
            if isinstance(saved_chunks, list):
                all_chunks.extend(saved_chunks)
            saved_mind = str(record.get('adviser_mind', '')).strip()
            if saved_mind:
                all_minds.append(saved_mind)
        combined_mind = '\n\n---\n\n'.join(all_minds)
        session.learn(all_chunks, combined_mind)
        return ('✓ Knowledge added', gr.update(visible=True), knowledge_library_text(user_id), knowledge_removal_choices(user_id))
    except Exception as error:
        print('Book learning error:', error)
        error_text = str(error).lower()
        if '429' in error_text or 'rate limit' in error_text:
            return ('AI usage limit reached. Please try adding this knowledge later.', gr.update(), knowledge_library_text(user_id), knowledge_removal_choices(user_id))
        return ("I couldn't read that file.", gr.update(), knowledge_library_text(user_id), knowledge_removal_choices(user_id))

def chat(message, history, session_id, user_id):
    message = str(message).strip()
    if not message:
        return ('', history)
    session = get_session(session_id, user_id)
    owner = memory_user_id(session_id, authenticated_user_id=user_id)
    memory_result = extract_memory(client, message, session.memory.as_text())
    action = memory_result.get('action', 'none')
    memory = memory_result.get('memory', '')
    old_memory = memory_result.get('old_memory', '')
    if action == 'add' and memory:
        session.memory.add(memory)
        save_memory(owner, memory)
    elif action == 'replace' and old_memory:
        session.memory.replace(old_memory, memory)
        replace_memory(owner, old_memory, memory)
    elif action == 'delete' and old_memory:
        session.memory.remove(old_memory)
        delete_memory(owner, old_memory)
    results = session.search(message, top_k=4)
    answer = generate_reply(client=client, message=message, conversation=session.conversation, adviser_mind=session.adviser_mind, retrieved_knowledge=results, memory_text=session.memory.as_text())
    session.conversation.append({'role': 'user', 'content': message})
    session.conversation.append({'role': 'assistant', 'content': answer})
    history = history or []
    history.append({'role': 'user', 'content': message})
    history.append({'role': 'assistant', 'content': answer})
    return ('', history)

def new_conversation(session_id, user_id):
    session = get_session(session_id, user_id)
    session.clear_conversation()
    return []

def show_upload():
    return gr.update(visible=True)
CUSTOM_CSS = '\n.gradio-container {\n    max-width: 760px !important;\n    margin: auto !important;\n}\n\n#title {\n    text-align: center;\n    margin-top: 18px;\n}\n\n#subtitle {\n    text-align: center;\n    opacity: 0.65;\n    margin-bottom: 14px;\n}\n\n#chatbot {\n    min-height: 62vh;\n}\n\n#composer {\n    position: sticky;\n    bottom: 0;\n    padding-top: 8px;\n}\n\nfooter {\n    display: none !important;\n}\n'

def ui_logout(session_id, user_id):
    """Destroy active in-memory session on logout."""
    if session_id and user_id:
        session_key = (str(session_id), str(user_id))
        user_sessions.pop(session_key, None)
    return (None, '', '', '', [], gr.update(visible=True), gr.update(visible=False))

def get_knowledge_library(user_id):
    """Return the authenticated user's saved knowledge sources."""
    if not user_id:
        return []
    records = load_user_knowledge(user_id)
    return [{'file_hash': record.get('file_hash'), 'file_name': record.get('file_name') or 'Untitled document', 'created_at': record.get('created_at')} for record in records]

def remove_knowledge_source(session_id, user_id, file_hash):
    """Delete one source and rebuild the user's active knowledge."""
    if not user_id or not file_hash:
        return False
    delete_user_knowledge(user_id, file_hash)
    session_key = (str(session_id), str(user_id))
    user_sessions.pop(session_key, None)
    session = get_session(session_id, user_id)
    records = load_user_knowledge(user_id)
    all_chunks = []
    all_minds = []
    for record in records:
        chunks = record.get('chunks', [])
        if isinstance(chunks, list):
            all_chunks.extend(chunks)
        mind = str(record.get('adviser_mind', '')).strip()
        if mind:
            all_minds.append(mind)
    if all_chunks:
        combined_mind = '\n\n---\n\n'.join(all_minds)
        session.learn(all_chunks, combined_mind)
    return True



def ui_remove_knowledge(file_hash, session_id, user_id):
    """Remove one saved knowledge source safely."""

    if not user_id:
        return (
            "Please log in first.",
            knowledge_library_text(user_id),
            knowledge_removal_choices(user_id)
        )

    if not file_hash:
        return (
            "Select a book to remove.",
            knowledge_library_text(user_id),
            knowledge_removal_choices(user_id)
        )

    try:
        remove_knowledge_source(
            session_id,
            user_id,
            file_hash
        )

        return (
            "✓ Knowledge removed",
            knowledge_library_text(user_id),
            knowledge_removal_choices(user_id)
        )

    except Exception as error:
        print("Knowledge removal error:", error)

        return (
            "I couldn't remove that knowledge.",
            knowledge_library_text(user_id),
            knowledge_removal_choices(user_id)
        )

def knowledge_removal_choices(user_id):
    """Return this user's books for the removal dropdown."""
    if not user_id:
        return gr.update(choices=[], value=None)
    library = get_knowledge_library(user_id)
    choices = []
    for item in library:
        file_name = str(item.get('file_name', 'Untitled document'))
        file_hash = str(item.get('file_hash', '')).strip()
        if file_hash:
            choices.append((file_name, file_hash))
    return gr.update(choices=choices, value=None)

def knowledge_library_text(user_id):
    """Create a simple display of the user's saved knowledge."""
    library = get_knowledge_library(user_id)
    if not library:
        return 'No knowledge added yet.'
    lines = ['### Your knowledge']
    for index, item in enumerate(library, start=1):
        file_name = item.get('file_name', 'Untitled document')
        lines.append(f'{index}. 📄 {file_name}')
    return '\n\n'.join(lines)

def restore_user_knowledge(session, user_id):
    """
    Restore persisted knowledge for one
    authenticated user into their session.
    """
    if not user_id:
        return 0
    records = load_user_knowledge(user_id)
    if not records:
        return 0
    all_chunks = []
    adviser_minds = []
    for record in records:
        chunks = record.get('chunks', [])
        if isinstance(chunks, list):
            all_chunks.extend(chunks)
        mind = str(record.get('adviser_mind', '')).strip()
        if mind:
            adviser_minds.append(mind)
    if not all_chunks:
        return 0
    if adviser_minds:
        combined_mind = '\n\n---\n\n'.join(adviser_minds)
    else:
        combined_mind = 'Use the restored knowledge as internal guidance.'
    session.learn(all_chunks, combined_mind)
    return len(records)

def restore_user_minds(user_id):
    """Return persisted Adviser Minds for one authenticated user."""
    if not user_id:
        return []
    records = load_user_knowledge(user_id)
    minds = []
    for record in records:
        adviser_mind = str(record.get('adviser_mind', '')).strip()
        if adviser_mind:
            minds.append(adviser_mind)
    return minds

def ui_login(username, password, session_id):
    result = login(username, password)
    if not result['success']:
        return (None, result['message'], gr.update(visible=True), gr.update(visible=False), 'No knowledge added yet.')
    user_id = result['user_id']
    session = get_session(session_id, user_id)
    restored = restore_user_knowledge(session, user_id)
    return (user_id, '✓ Logged in' if restored == 0 else f'✓ Logged in · {restored} knowledge source(s) restored', gr.update(visible=False), gr.update(visible=True), knowledge_library_text(user_id))

def ui_signup(username, password):
    result = signup(username, password)
    if not result['success']:
        return (None, result['message'], gr.update(visible=True), gr.update(visible=False))
    return (result['user_id'], '✓ Account created', gr.update(visible=False), gr.update(visible=True), 'No knowledge added yet.')

app_css = """
/* ===== Adviser AI Knowledge Library ===== */

#knowledge-library {
    margin-top: 12px;
    padding: 14px;
    border: 1px solid rgba(128, 128, 128, 0.18);
    border-radius: 16px;
}

#knowledge-library h3 {
    margin-bottom: 8px;
}

#knowledge-remove-select {
    margin-top: 8px;
}

#knowledge-library button {
    min-height: 36px;
    border-radius: 10px;
}

#knowledge-library .prose {
    font-size: 0.92rem;
    line-height: 1.45;
}

@media (max-width: 600px) {
    #knowledge-library {
        padding: 10px;
        border-radius: 14px;
    }
}
"""

with gr.Blocks(css=app_css) as app:
    session_state = gr.State(create_session_id)
    user_state = gr.State(None)
    with gr.Column(visible=True, elem_id='auth-panel') as auth_panel:
        gr.Markdown('## Welcome to Adviser')
        gr.Markdown('Log in or create an account to continue.')
        auth_username = gr.Textbox(label='Username', placeholder='Enter username')
        auth_password = gr.Textbox(label='Password', type='password', placeholder='Enter password')
        auth_status = gr.Markdown('')
        with gr.Row():
            login_button = gr.Button('Log in', variant='primary')
            signup_button = gr.Button('Sign up')
    with gr.Column(visible=False, elem_id='adviser-panel') as adviser_panel:
        gr.Markdown('# Adviser', elem_id='title')
        logout_button = gr.Button('Log out', size='sm')
        with gr.Column(elem_id='knowledge-library'):
            gr.Markdown('### Knowledge')
            knowledge_display = gr.Markdown('No knowledge added yet.')
            knowledge_remove_select = gr.Dropdown(label='Remove knowledge', choices=[], value=None, interactive=True, elem_id='knowledge-remove-select')
            knowledge_remove_button = gr.Button('Remove selected', size='sm')
        gr.Markdown('AI adviser', elem_id='subtitle')
        with gr.Row():
            add_button = gr.Button('+', scale=0)
            new_button = gr.Button('↻', scale=0)
        with gr.Column(visible=False) as upload_panel:
            upload = gr.File(label='Add knowledge', file_types=['.pdf'])
            learn_button = gr.Button('Add')
            upload_status = gr.Markdown()
        chatbot = gr.Chatbot(elem_id='chatbot')
        with gr.Row(elem_id='composer'):
            message = gr.Textbox(placeholder='Message...', show_label=False, scale=8)
            send = gr.Button('↑', scale=1)
        add_button.click(show_upload, outputs=upload_panel)
    logout_button.click(ui_logout, inputs=[session_state, user_state], outputs=[user_state, auth_username, auth_password, auth_status, chatbot, auth_panel, adviser_panel])
    login_button.click(ui_login, inputs=[auth_username, auth_password, session_state], outputs=[user_state, auth_status, auth_panel, adviser_panel, knowledge_display])
    signup_button.click(ui_signup, inputs=[auth_username, auth_password], outputs=[user_state, auth_status, auth_panel, adviser_panel, knowledge_display])
    knowledge_remove_button.click(
        ui_remove_knowledge,
        inputs=[
            knowledge_remove_select,
            session_state,
            user_state
        ],
        outputs=[
            upload_status,
            knowledge_display,
            knowledge_remove_select
        ]
    )

    learn_button.click(learn_book, inputs=[upload, session_state, user_state], outputs=[upload_status, upload_panel, knowledge_display, knowledge_remove_select]).then(reset_upload_file, outputs=[upload])
    send.click(chat, inputs=[message, chatbot, session_state, user_state], outputs=[message, chatbot])
    message.submit(chat, inputs=[message, chatbot, session_state, user_state], outputs=[message, chatbot])
    new_button.click(new_conversation, inputs=[session_state, user_state], outputs=chatbot)
if __name__ == '__main__':
    app.launch(share=True, css=CUSTOM_CSS, theme=gr.themes.Base())
