"""Add memory architecture tables

Revision ID: e985bdea3de9
Revises: 4838883a80a9
Create Date: 2026-01-30 12:42:32.476768

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'e985bdea3de9'
down_revision: Union[str, Sequence[str], None] = '4838883a80a9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Add User columns
    op.add_column('users', sa.Column('preferences', postgresql.JSONB(astext_type=sa.Text()), nullable=True))
    op.add_column('users', sa.Column('traits', postgresql.JSONB(astext_type=sa.Text()), nullable=True))

    # Create Facts
    op.create_table('facts',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('category', sa.String(), nullable=False),
        sa.Column('value', sa.Text(), nullable=False),
        sa.Column('confidence_score', sa.Float(), nullable=True),
        sa.Column('source_message_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('metadata', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('last_reinforced_at', sa.DateTime(), nullable=True),
        sa.Column('reinforcement_count', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )

    # Create Episodic Memories
    op.create_table('episodic_memories',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('summary', sa.Text(), nullable=False),
        sa.Column('vector_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('emotions', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('topics', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('importance_score', sa.Float(), nullable=True),
        sa.Column('context_type', sa.String(), nullable=True),
        sa.Column('decay_factor', sa.Float(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table('episodic_memories')
    op.drop_table('facts')
    op.drop_column('users', 'traits')
    op.drop_column('users', 'preferences')
