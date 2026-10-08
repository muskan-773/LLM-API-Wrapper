# LLM API Wrapper — Architecture

## 1. Overview

The LLM API Wrapper is a FastAPI backend that demonstrates how an
LLM-powered service can be structured using production-style backend
patterns.

The current implementation uses a mock LLM provider.

The main components are:

- FastAPI
- LLM service
- Redis cache
- PostgreSQL database
- Retry service
- Usage tracking
- SSE streaming
- Configuration validation

The system is designed so that HTTP handling, business logic,
infrastructure, and data models remain separated.

---

## 2. High-Level Architecture

```text
                         Client
                           |
                           v
                    +-------------+
                    |   FastAPI   |
                    |    Routes   |
                    +-------------+
                           |
                           v
                    +-------------+
                    | LLM Service |
                    +-------------+
                       /    |    \
                      /     |     \
                     v      v      v
                 Redis   Mock LLM  Retry
                 Cache             Logic
                    |
                    |
                    v
              Usage Store
                    |
                    v
               PostgreSQL