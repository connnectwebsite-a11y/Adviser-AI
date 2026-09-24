# Adviser AI

Adviser AI is a conversational AI system that transforms user-uploaded books and documents into a persistent, personalized AI adviser.

Rather than functioning as a simple chat-with-PDF application, Adviser AI extracts knowledge and principles from uploaded material and uses them to support natural conversations about both the source material and new situations.

## Features

- User signup and login
- Secure password hashing
- Multi-user data isolation
- Multiple PDF/books per account
- Semantic retrieval with vector embeddings
- FAISS vector search
- Adviser Mind generation
- Persistent knowledge library
- Persistent user memory
- Conversation context
- Knowledge restoration after login/restart
- Individual knowledge-source removal
- Automatic knowledge rebuilding after deletion
- Mobile-friendly Gradio interface
- Groq-powered conversational responses

## Architecture

User
→ Gradio Interface
→ Authentication / PDF Upload
→ Text Extraction
→ Chunking
→ Sentence Transformer Embeddings
→ FAISS Retrieval
→ Adviser Mind + Persistent Memory
→ Conversation Engine
→ Groq LLM
→ AI Response

## Technology Stack

- Python
- Gradio
- Groq API
- PyMuPDF
- Sentence Transformers
- FAISS
- SQLite
- NumPy

## Core Components

### Knowledge Engine

Creates embeddings from document chunks and performs semantic retrieval using FAISS.

### Adviser Mind

Extracts higher-level ideas and principles from uploaded material so the adviser can apply the material to situations beyond direct document lookup.

### Persistent Memory

Stores durable user information such as preferences, goals, projects and explicitly remembered information.

### Conversation Engine

Combines relevant document knowledge, Adviser Mind, persistent memory and recent conversation history to produce context-aware responses.

### Authentication

Provides prototype account creation, password hashing, login and user-specific data separation.

## Running Locally

Install the dependencies with:

    pip install -r requirements.txt

Set the GROQ_API_KEY environment variable, then run:

    python app.py

## Privacy

API credentials are not included in this repository.

User databases, uploaded documents, generated knowledge caches and other user-specific data are excluded from version control.

## Current Status

Adviser AI v1 is a working portfolio prototype demonstrating document ingestion, retrieval-augmented generation, persistent knowledge, persistent memory, multi-user authentication, multi-document reasoning and conversational AI.

## Production Roadmap

- Managed authentication
- PostgreSQL or another production database
- Production vector storage
- Durable document storage
- Stronger session management
- Rate limiting and monitoring
- Automated testing
- Production secrets management
- Dedicated web frontend
- Scalable deployment infrastructure

## Purpose

Adviser AI was built as an AI engineering portfolio project exploring retrieval-augmented generation, persistent memory, document intelligence, multi-user application architecture and conversational AI.
