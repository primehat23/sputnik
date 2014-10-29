"""add prediction contract support

Revision ID: 4bbfd8b1e4b3
Revises: None
Create Date: 2014-04-30 10:33:20.472308

"""

# revision identifiers, used by Alembic.
revision = '4bbfd8b1e4b3'
down_revision = None

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

def upgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.add_column('addresses', sa.Column('contract_id', sa.Integer(), nullable=True))
    op.drop_column('addresses', u'currency')
    op.add_column('contracts', sa.Column('payout_contract_ticker', sa.String(), nullable=True))
    op.add_column('contracts', sa.Column('expired', sa.Boolean(), server_default='false', nullable=True))
    op.add_column('contracts', sa.Column('denominated_contract_ticker', sa.String(), nullable=True))
    op.add_column('withdrawals', sa.Column('contract_id', sa.Integer(), nullable=True))
    op.drop_column('withdrawals', u'currency_id')
    ### end Alembic commands ###


def downgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.add_column('withdrawals', sa.Column(u'currency_id', sa.INTEGER(), nullable=True))
    op.drop_column('withdrawals', 'contract_id')
    op.drop_column('contracts', 'denominated_contract_ticker')
    op.drop_column('contracts', 'expired')
    op.drop_column('contracts', 'payout_contract_ticker')
    op.add_column('addresses', sa.Column(u'currency', postgresql.ENUM(u'btc', u'ltc', u'xrp', u'usd', u'mxn'), nullable=False))
    op.drop_column('addresses', 'contract_id')
    ### end Alembic commands ###
