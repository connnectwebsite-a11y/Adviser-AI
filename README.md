# Adviser AI

Adviser AI is a conversational AI adviser that learns
reasoning frameworks from user-provided documents.

Rather than simply answering questions about a PDF,
Adviser AI builds an internal "Adviser Mind" from the
document's principles, values, reasoning patterns,
decision rules, cautions, and recurring themes.

The user can then have a natural conversation with the
adviser and apply those principles to new situations.

## Current v1 Features

- PDF knowledge upload
- PDF text extraction with PyMuPDF
- Semantic chunk retrieval
- SentenceTransformer embeddings
- FAISS vector search
- Adviser Mind synthesis
- Large-document recursive synthesis
- mind-v2 persistent synthesis cache
- Natural Groq-powered conversation
- Conversation context
- Persistent long-term user memory
- Add, replace, and delete memories
- SQLite persistence
- Google Drive persistence in Colab
- Gradio conversational interface
- New-conversation reset
- Friendly rate-limit handling

## AI Model

Conversation and Adviser Mind synthesis currently use:

openai/gpt-oss-20b through Groq.

Embeddings use:

all-MiniLM-L6-v2

## Architecture

PDF
  -> text extraction
  -> chunks
  -> embeddings
  -> FAISS semantic index

PDF
  -> section analysis
  -> recursive reduction
  -> Adviser Mind
  -> persistent mind-v2 cache

User message
  -> memory extraction
  -> semantic retrieval
  -> Adviser Mind
  -> conversation history
  -> AI response

## Persistent Data

Long-term memory database:

/content/drive/MyDrive/AdviserAI/data/adviser.db

Adviser Mind cache:

/content/drive/MyDrive/AdviserAI/mind_cache

Permanent source:

/content/drive/MyDrive/AdviserAI/source

## Development Warning

The current development identity uses:

adviser_dev_user

This is suitable only for single-user development.

Before public multi-user deployment, replace it with
real authentication and per-user identities.

The current SQLite/Google Drive architecture is also
intended for development rather than concurrent public
production.

## Product Principle

Upload in seconds.
Forget the technology.
Have a conversation.
