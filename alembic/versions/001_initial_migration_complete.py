"""Initial migration complete

Revision ID: 001
Revises: 
Create Date: 2024-01-01 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create enum types
    userrole = postgresql.ENUM('freelancer', 'client', 'both', 'admin', name='userrole')
    userrole.create(op.get_bind())
    
    verificationstatus = postgresql.ENUM('unverified', 'email_verified', 'diia_verified', name='verificationstatus')
    verificationstatus.create(op.get_bind())
    
    subscriptiontype = postgresql.ENUM('free', 'freelancer_plus', name='subscriptiontype')
    subscriptiontype.create(op.get_bind())
    
    projectstatus = postgresql.ENUM('draft', 'open', 'in_progress', 'completed', 'cancelled', 'disputed', name='projectstatus')
    projectstatus.create(op.get_bind())
    
    projecttype = postgresql.ENUM('fixed_price', 'hourly', name='projecttype')
    projecttype.create(op.get_bind())
    
    projectduration = postgresql.ENUM('less_than_week', 'less_than_month', 'one_to_three_months', 'three_to_six_months', 'more_than_six_months', name='projectduration')
    projectduration.create(op.get_bind())
    
    experiencelevel = postgresql.ENUM('entry', 'intermediate', 'expert', name='experiencelevel')
    experiencelevel.create(op.get_bind())
    
    proposalstatus = postgresql.ENUM('pending', 'accepted', 'rejected', 'withdrawn', name='proposalstatus')
    proposalstatus.create(op.get_bind())
    
    transactiontype = postgresql.ENUM('escrow_fund', 'escrow_release', 'escrow_refund', 'milestone_fund', 'milestone_release', 'connects_purchase', 'subscription_payment', 'profile_promotion', 'withdrawal', 'commission', name='transactiontype')
    transactiontype.create(op.get_bind())
    
    transactionstatus = postgresql.ENUM('pending', 'processing', 'completed', 'failed', 'cancelled', 'refunded', name='transactionstatus')
    transactionstatus.create(op.get_bind())
    
    paymentmethod = postgresql.ENUM('monobank', 'card', 'bank_transfer', name='paymentmethod')
    paymentmethod.create(op.get_bind())
    
    timeentrystatus = postgresql.ENUM('pending', 'approved', 'rejected', 'paid', name='timeentrystatus')
    timeentrystatus.create(op.get_bind())
    
    # Create tables
    op.create_table('users',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('username', sa.String(length=100), nullable=False),
        sa.Column('hashed_password', sa.String(length=255), nullable=False),
        sa.Column('first_name', sa.String(length=100), nullable=True),
        sa.Column('last_name', sa.String(length=100), nullable=True),
        sa.Column('phone', sa.String(length=20), nullable=True),
        sa.Column('avatar_url', sa.String(length=500), nullable=True),
        sa.Column('role', sa.Enum('freelancer', 'client', 'both', 'admin', name='userrole'), nullable=False),
        sa.Column('verification_status', sa.Enum('unverified', 'email_verified', 'diia_verified', name='verificationstatus'), nullable=True),
        sa.Column('diia_request_id', sa.String(length=255), nullable=True),
        sa.Column('title', sa.String(length=200), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('hourly_rate', sa.Float(), nullable=True),
        sa.Column('skills', sa.JSON(), nullable=True),
        sa.Column('portfolio_items', sa.JSON(), nullable=True),
        sa.Column('categories', sa.JSON(), nullable=True),
        sa.Column('total_earned', sa.Float(), nullable=True),
        sa.Column('total_spent', sa.Float(), nullable=True),
        sa.Column('jobs_completed', sa.Integer(), nullable=True),
        sa.Column('rating', sa.Float(), nullable=True),
        sa.Column('reviews_count', sa.Integer(), nullable=True),
        sa.Column('connects_balance', sa.Integer(), nullable=True),
        sa.Column('subscription_type', sa.Enum('free', 'freelancer_plus', name='subscriptiontype'), nullable=True),
        sa.Column('subscription_expires_at', sa.DateTime(), nullable=True),
        sa.Column('profile_promoted_until', sa.DateTime(), nullable=True),
        sa.Column('earnings_with_client', sa.JSON(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.Column('is_online', sa.Boolean(), nullable=True),
        sa.Column('last_seen_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=True)
    op.create_index(op.f('ix_users_id'), 'users', ['id'], unique=False)
    op.create_index(op.f('ix_users_username'), 'users', ['username'], unique=True)
    
    op.create_table('projects',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('client_id', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(length=200), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('category', sa.String(length=100), nullable=False),
        sa.Column('subcategory', sa.String(length=100), nullable=True),
        sa.Column('project_type', sa.Enum('fixed_price', 'hourly', name='projecttype'), nullable=False),
        sa.Column('budget_min', sa.Float(), nullable=True),
        sa.Column('budget_max', sa.Float(), nullable=True),
        sa.Column('hourly_rate_min', sa.Float(), nullable=True),
        sa.Column('hourly_rate_max', sa.Float(), nullable=True),
        sa.Column('duration', sa.Enum('less_than_week', 'less_than_month', 'one_to_three_months', 'three_to_six_months', 'more_than_six_months', name='projectduration'), nullable=True),
        sa.Column('experience_level', sa.Enum('entry', 'intermediate', 'expert', name='experiencelevel'), nullable=True),
        sa.Column('skills_required', sa.JSON(), nullable=True),
        sa.Column('attachments', sa.JSON(), nullable=True),
        sa.Column('connects_to_apply', sa.Integer(), nullable=True),
        sa.Column('proposals_limit', sa.Integer(), nullable=True),
        sa.Column('status', sa.Enum('draft', 'open', 'in_progress', 'completed', 'cancelled', 'disputed', name='projectstatus'), nullable=True),
        sa.Column('is_urgent', sa.Boolean(), nullable=True),
        sa.Column('is_featured', sa.Boolean(), nullable=True),
        sa.Column('selected_freelancer_id', sa.Integer(), nullable=True),
        sa.Column('views_count', sa.Integer(), nullable=True),
        sa.Column('proposals_count', sa.Integer(), nullable=True),
        sa.Column('escrow_funded', sa.Boolean(), nullable=True),
        sa.Column('escrow_amount', sa.Float(), nullable=True),
        sa.Column('milestones', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.Column('published_at', sa.DateTime(), nullable=True),
        sa.Column('deadline', sa.DateTime(), nullable=True),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['client_id'], ['users.id'], ),
        sa.ForeignKeyConstraint(['selected_freelancer_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_projects_category'), 'projects', ['category'], unique=False)
    op.create_index(op.f('ix_projects_id'), 'projects', ['id'], unique=False)
    op.create_index(op.f('ix_projects_title'), 'projects', ['title'], unique=False)
    
    op.create_table('messages',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('sender_id', sa.Integer(), nullable=False),
        sa.Column('receiver_id', sa.Integer(), nullable=False),
        sa.Column('project_id', sa.Integer(), nullable=True),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('attachments', sa.Text(), nullable=True),
        sa.Column('is_read', sa.Boolean(), nullable=True),
        sa.Column('read_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ),
        sa.ForeignKeyConstraint(['receiver_id'], ['users.id'], ),
        sa.ForeignKeyConstraint(['sender_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    op.create_table('proposals',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('project_id', sa.Integer(), nullable=False),
        sa.Column('freelancer_id', sa.Integer(), nullable=False),
        sa.Column('cover_letter', sa.Text(), nullable=False),
        sa.Column('proposed_amount', sa.Float(), nullable=True),
        sa.Column('proposed_hourly_rate', sa.Float(), nullable=True),
        sa.Column('estimated_duration', sa.String(length=100), nullable=True),
        sa.Column('proposed_milestones', sa.Text(), nullable=True),
        sa.Column('attachments', sa.Text(), nullable=True),
        sa.Column('status', sa.Enum('pending', 'accepted', 'rejected', 'withdrawn', name='proposalstatus'), nullable=True),
        sa.Column('connects_spent', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['freelancer_id'], ['users.id'], ),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    op.create_table('reviews',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('project_id', sa.Integer(), nullable=False),
        sa.Column('reviewer_id', sa.Integer(), nullable=False),
        sa.Column('reviewee_id', sa.Integer(), nullable=False),
        sa.Column('rating', sa.Float(), nullable=False),
        sa.Column('comment', sa.Text(), nullable=True),
        sa.Column('quality_rating', sa.Float(), nullable=True),
        sa.Column('communication_rating', sa.Float(), nullable=True),
        sa.Column('expertise_rating', sa.Float(), nullable=True),
        sa.Column('professionalism_rating', sa.Float(), nullable=True),
        sa.Column('deadline_rating', sa.Float(), nullable=True),
        sa.Column('would_hire_again', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ),
        sa.ForeignKeyConstraint(['reviewee_id'], ['users.id'], ),
        sa.ForeignKeyConstraint(['reviewer_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    op.create_table('transactions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('payer_id', sa.Integer(), nullable=True),
        sa.Column('payee_id', sa.Integer(), nullable=True),
        sa.Column('project_id', sa.Integer(), nullable=True),
        sa.Column('transaction_type', sa.Enum('escrow_fund', 'escrow_release', 'escrow_refund', 'milestone_fund', 'milestone_release', 'connects_purchase', 'subscription_payment', 'profile_promotion', 'withdrawal', 'commission', name='transactiontype'), nullable=False),
        sa.Column('amount', sa.Float(), nullable=False),
        sa.Column('currency', sa.String(length=3), nullable=True),
        sa.Column('commission_amount', sa.Float(), nullable=True),
        sa.Column('commission_rate', sa.Float(), nullable=True),
        sa.Column('net_amount', sa.Float(), nullable=True),
        sa.Column('payment_method', sa.Enum('monobank', 'card', 'bank_transfer', name='paymentmethod'), nullable=True),
        sa.Column('monobank_invoice_id', sa.String(length=255), nullable=True),
        sa.Column('monobank_transaction_id', sa.String(length=255), nullable=True),
        sa.Column('status', sa.Enum('pending', 'processing', 'completed', 'failed', 'cancelled', 'refunded', name='transactionstatus'), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('extra_data', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['payee_id'], ['users.id'], ),
        sa.ForeignKeyConstraint(['payer_id'], ['users.id'], ),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('monobank_invoice_id')
    )
    
    op.create_table('time_entries',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('project_id', sa.Integer(), nullable=False),
        sa.Column('freelancer_id', sa.Integer(), nullable=False),
        sa.Column('start_time', sa.DateTime(), nullable=False),
        sa.Column('end_time', sa.DateTime(), nullable=False),
        sa.Column('hours_worked', sa.Float(), nullable=False),
        sa.Column('hourly_rate', sa.Float(), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('screenshot_urls', sa.Text(), nullable=True),
        sa.Column('activity_level', sa.Float(), nullable=True),
        sa.Column('status', sa.Enum('pending', 'approved', 'rejected', 'paid', name='timeentrystatus'), nullable=True),
        sa.Column('amount', sa.Float(), nullable=False),
        sa.Column('transaction_id', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('approved_at', sa.DateTime(), nullable=True),
        sa.Column('paid_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['freelancer_id'], ['users.id'], ),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ),
        sa.ForeignKeyConstraint(['transaction_id'], ['transactions.id'], ),
        sa.PrimaryKeyConstraint('id')
    )


def downgrade() -> None:
    # Drop tables
    op.drop_table('time_entries')
    op.drop_table('transactions')
    op.drop_table('reviews')
    op.drop_table('proposals')
    op.drop_table('messages')
    op.drop_table('projects')
    op.drop_table('users')
    
    # Drop enum types
    op.execute('DROP TYPE IF EXISTS userrole')
    op.execute('DROP TYPE IF EXISTS verificationstatus')
    op.execute('DROP TYPE IF EXISTS subscriptiontype')
    op.execute('DROP TYPE IF EXISTS projectstatus')
    op.execute('DROP TYPE IF EXISTS projecttype')
    op.execute('DROP TYPE IF EXISTS projectduration')
    op.execute('DROP TYPE IF EXISTS experiencelevel')
    op.execute('DROP TYPE IF EXISTS proposalstatus')
    op.execute('DROP TYPE IF EXISTS transactiontype')
    op.execute('DROP TYPE IF EXISTS transactionstatus')
    op.execute('DROP TYPE IF EXISTS paymentmethod')
    op.execute('DROP TYPE IF EXISTS timeentrystatus')