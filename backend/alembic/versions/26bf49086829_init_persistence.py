from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql as psql

revision = "<rev>"
down_revision = None
branch_labels = None
depends_on = None

def upgrade() -> None:
    op.create_table(
        "sessions",
        sa.Column("session_id", sa.Text, primary_key=True),
        sa.Column("user_id", sa.Text),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("NOW()"), nullable=False),
        sa.Column("updated_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("NOW()"), nullable=False),
        sa.Column("technique", sa.Text),
        sa.Column("difficulty", sa.Text),
        sa.Column("current_step", sa.Integer),
        sa.Column("phase", sa.Text),
        sa.Column("score", sa.Integer),
        sa.Column("accuracy_rate", sa.Float),
        sa.Column("hints_used", sa.Integer),
        sa.Column("bandit", psql.JSONB),
        sa.Column("rolling_stats", psql.JSONB),
        sa.Column("state", psql.JSONB, nullable=False),
    )
    op.create_index("sessions_updated_at_idx", "sessions", ["updated_at"])
    op.create_index("sessions_user_id_idx", "sessions", ["user_id"])

    op.create_table(
        "answers",
        sa.Column("id", sa.BigInteger, primary_key=True, autoincrement=True),
        sa.Column("session_id", sa.Text, sa.ForeignKey("sessions.session_id", ondelete="CASCADE")),
        sa.Column("question_id", sa.Text),
        sa.Column("step_number", sa.Integer),
        sa.Column("user_answer", psql.JSONB),
        sa.Column("correct", sa.Boolean),
        sa.Column("rt_seconds", sa.Float),
        sa.Column("revealed", sa.Boolean),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("NOW()"), nullable=False),
    )
    op.create_index("answers_session_idx", "answers", ["session_id", "created_at"])

    op.create_table(
        "checkpoints",
        sa.Column("id", sa.BigInteger, primary_key=True, autoincrement=True),
        sa.Column("session_id", sa.Text, sa.ForeignKey("sessions.session_id", ondelete="CASCADE")),
        sa.Column("tag", sa.Text),
        sa.Column("snapshot", psql.JSONB, nullable=False),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("NOW()"), nullable=False),
    )
    op.create_index("checkpoints_session_idx", "checkpoints", ["session_id", "created_at"])


def downgrade() -> None:
    op.drop_index("checkpoints_session_idx", table_name="checkpoints")
    op.drop_table("checkpoints")
    op.drop_index("answers_session_idx", table_name="answers")
    op.drop_table("answers")
    op.drop_index("sessions_user_id_idx", table_name="sessions")
    op.drop_index("sessions_updated_at_idx", table_name="sessions")
    op.drop_table("sessions")
