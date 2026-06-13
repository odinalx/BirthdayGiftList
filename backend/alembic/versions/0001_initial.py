"""initial

Revision ID: 0001
Revises:
Create Date: 2024-01-01 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op

revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("CREATE TYPE giftstatus AS ENUM ('AVAILABLE', 'RESERVED', 'BOUGHT')")

    op.execute("""
        CREATE TABLE users (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            google_id VARCHAR(255) NOT NULL,
            email VARCHAR(255) NOT NULL,
            name VARCHAR(255) NOT NULL,
            picture VARCHAR(500),
            list_slug VARCHAR(50) NOT NULL,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
            CONSTRAINT uq_users_google_id UNIQUE (google_id),
            CONSTRAINT uq_users_email UNIQUE (email),
            CONSTRAINT uq_users_list_slug UNIQUE (list_slug)
        )
    """)
    op.execute("CREATE INDEX ix_users_google_id ON users (google_id)")
    op.execute("CREATE INDEX ix_users_email ON users (email)")
    op.execute("CREATE INDEX ix_users_list_slug ON users (list_slug)")

    op.execute("""
        CREATE TABLE gifts (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            title VARCHAR(255) NOT NULL,
            description TEXT,
            image_url VARCHAR(1000),
            link VARCHAR(1000),
            price NUMERIC(10, 2),
            status giftstatus NOT NULL DEFAULT 'AVAILABLE',
            claimed_by_name VARCHAR(255),
            claimed_by_visitor_id VARCHAR(255),
            created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL
        )
    """)


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS gifts")
    op.execute("DROP TABLE IF EXISTS users")
    op.execute("DROP TYPE IF EXISTS giftstatus")
