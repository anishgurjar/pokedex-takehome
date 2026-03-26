"""remove_pokemon_habitat

Revision ID: 4235c1ee08ed
Revises: 1a18e259c72c

"""

from collections.abc import Sequence

# revision identifiers, used by Alembic.
revision: str = "4235c1ee08ed"
down_revision: str | Sequence[str] | None = "1a18e259c72c"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
