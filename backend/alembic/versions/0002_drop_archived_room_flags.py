"""Drop habit archive feature; add room visibility flags.

Revision ID: 0002
Revises: 0001
Create Date: 2026-07-08
"""

import sqlalchemy as sa
from alembic import op

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 0001 creates the schema from live ORM metadata, so a fresh database
    # already matches the new schema — every op must be inspector-guarded.
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    habit_indexes = {i["name"] for i in inspector.get_indexes("habits")}
    if "ix_habits_user_archived_position" in habit_indexes:
        op.drop_index("ix_habits_user_archived_position", table_name="habits")

    if "archived" in {c["name"] for c in inspector.get_columns("habits")}:
        with op.batch_alter_table("habits") as batch:
            batch.drop_column("archived")

    # Batch mode recreates the table, dropping its indexes — re-inspect.
    habit_indexes = {i["name"] for i in sa.inspect(bind).get_indexes("habits")}
    if "ix_habits_user_position" not in habit_indexes:
        op.create_index("ix_habits_user_position", "habits", ["user_id", "position"])

    if "archived" in {c["name"] for c in inspector.get_columns("room_habits")}:
        with op.batch_alter_table("room_habits") as batch:
            batch.drop_column("archived")

    room_cols = {c["name"] for c in inspector.get_columns("rooms")}
    with op.batch_alter_table("rooms") as batch:
        if "show_leaderboard" not in room_cols:
            batch.add_column(sa.Column("show_leaderboard", sa.Boolean(), nullable=False, server_default="1"))
        if "show_members" not in room_cols:
            batch.add_column(sa.Column("show_members", sa.Boolean(), nullable=False, server_default="1"))


def downgrade() -> None:
    with op.batch_alter_table("rooms") as batch:
        batch.drop_column("show_members")
        batch.drop_column("show_leaderboard")
    with op.batch_alter_table("room_habits") as batch:
        batch.add_column(sa.Column("archived", sa.Boolean(), nullable=False, server_default="0"))
    op.drop_index("ix_habits_user_position", table_name="habits")
    with op.batch_alter_table("habits") as batch:
        batch.add_column(sa.Column("archived", sa.Boolean(), nullable=False, server_default="0"))
    op.create_index("ix_habits_user_archived_position", "habits", ["user_id", "archived", "position"])
