"""categories.icon — emoji o'rniga ikonka nomi

Revision ID: e5f6a7b8c9d0
Revises: d4e5f6a7b8c9
Create Date: 2026-09-01 16:00:00.000000

Ustun turi o'zgarmaydi (VARCHAR). Mavjud emojilar ikonka nomlariga
ko'chiriladi (maket 7-bo'lim). Ro'yxatda yo'q emoji -> 'tool'.

Downgrade: QAYTARILMAYDI (emoji ma'lumoti yo'qolgan). Frontend nomni
topa olmasa 'tool' + kulrang ishlatadi, yiqilmaydi.
"""
from collections.abc import Sequence

from alembic import op


revision: str = 'e5f6a7b8c9d0'
down_revision: str | None = 'd4e5f6a7b8c9'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute(
        """
        UPDATE categories SET icon = CASE
            WHEN icon IN ('🏠') THEN 'stack-2'
            WHEN icon IN ('🧱') THEN 'wall'
            WHEN icon IN ('⬜') THEN 'layout-grid'
            WHEN icon IN ('◻️', '◻') THEN 'checkbox'
            WHEN icon IN ('⚡') THEN 'bolt'
            WHEN icon IN ('🚿') THEN 'droplet'
            WHEN icon IN ('🔨') THEN 'hammer'
            WHEN icon IN ('📋') THEN 'tool'
            WHEN icon IN ('🪣') THEN 'bucket'
            WHEN icon IN ('🎨') THEN 'brush'
            WHEN icon IN ('📦') THEN 'package'
            ELSE 'tool'
        END
        WHERE icon IS NOT NULL AND icon <> ''
        """
    )


def downgrade() -> None:
    # Emoji -> nom ko'chirish qaytarilmaydi.
    pass
