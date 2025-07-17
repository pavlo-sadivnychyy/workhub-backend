"""
WorkHub.ua API Package

This package contains all API endpoints organized by domain:
- auth: Authentication and authorization
- users: User management and profiles
- projects: Project CRUD and search
- proposals: Proposal submission and management
- payments: Payment processing and transactions
- reviews: Review system
"""

from app.api import auth, users, projects, proposals, payments, reviews

__all__ = ["auth", "users", "projects", "proposals", "payments", "reviews"]