"""make_email_normalized_unique

Revision ID: 3f1e2d4c5b6a
Revises: b6f7c8d9e0f1
Create Date: 2026-03-26 11:45:00.000000

"""

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "3f1e2d4c5b6a"
down_revision: str | Sequence[str] | None = "b6f7c8d9e0f1"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    duplicates = (
        op.get_bind()
        .exec_driver_sql(
            """
        SELECT email_normalized
        FROM app_users
        GROUP BY email_normalized
        HAVING COUNT(*) > 1
        """
        )
        .fetchall()
    )
    if duplicates:
        raise RuntimeError(
            "Cannot add unique app_users.email_normalized index while duplicates exist"
        )

    with op.batch_alter_table("app_users", recreate="always") as batch_op:
        batch_op.drop_index("idx_app_users_email_norm")
        batch_op.create_index(
            "idx_app_users_email_norm",
            ["email_normalized"],
            unique=True,
        )


def downgrade() -> None:
    with op.batch_alter_table("app_users", recreate="always") as batch_op:
        batch_op.drop_index("idx_app_users_email_norm")
        batch_op.create_index(
            "idx_app_users_email_norm",
            ["email_normalized"],
            unique=False,
        )
