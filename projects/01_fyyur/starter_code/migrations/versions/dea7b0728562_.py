"""empty message

Revision ID: dea7b0728562
Revises: 4d8a4a76f2cf
Create Date: 2021-08-03 10:40:36.739796

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'dea7b0728562'
down_revision = '4d8a4a76f2cf'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column('Show', 'venue_id',
               existing_type=sa.INTEGER(),
               nullable=False)
    op.alter_column('Show', 'artist_id',
               existing_type=sa.INTEGER(),
               nullable=False)
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column('Show', 'artist_id',
               existing_type=sa.INTEGER(),
               nullable=True)
    op.alter_column('Show', 'venue_id',
               existing_type=sa.INTEGER(),
               nullable=True)
    # ### end Alembic commands ###
