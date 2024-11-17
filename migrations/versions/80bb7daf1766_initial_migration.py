"""Initial migration

Revision ID: 80bb7daf1766
Revises: 
Create Date: 2024-11-17 21:38:53.434802

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '80bb7daf1766'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('category',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(length=100), nullable=False),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('name')
    )
    op.create_table('customer',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('full_name', sa.String(length=100), nullable=False),
    sa.Column('email', sa.String(length=100), nullable=False),
    sa.Column('username', sa.String(length=100), nullable=False),
    sa.Column('password_hash', sa.String(length=200), nullable=False),
    sa.Column('date_joined', sa.DateTime(), nullable=True),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('email'),
    sa.UniqueConstraint('username')
    )
    op.create_table('sub_category',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(length=100), nullable=False),
    sa.Column('category_id', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['category_id'], ['category.id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('name')
    )
    op.create_table('product',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('product_name', sa.String(length=100), nullable=False),
    sa.Column('author', sa.String(length=100), nullable=False),
    sa.Column('rating', sa.Float(), nullable=False),
    sa.Column('current_price', sa.Float(), nullable=False),
    sa.Column('in_stock', sa.Integer(), nullable=False),
    sa.Column('low_stock_threshold', sa.Integer(), nullable=True),
    sa.Column('warehouse_location', sa.String(length=100), nullable=False),
    sa.Column('promotion_percentage', sa.Integer(), nullable=True),
    sa.Column('discounted_price', sa.Float(), nullable=True),
    sa.Column('product_picture', sa.String(length=1000), nullable=False),
    sa.Column('flash_sale', sa.Boolean(), nullable=True),
    sa.Column('date_added', sa.DateTime(), nullable=True),
    sa.Column('category_id', sa.Integer(), nullable=False),
    sa.Column('subcategory_id', sa.Integer(), nullable=False),
    sa.Column('last_stock_update', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['category_id'], ['category.id'], ),
    sa.ForeignKeyConstraint(['subcategory_id'], ['sub_category.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('cart',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('quantity', sa.Integer(), nullable=False),
    sa.Column('customer_link', sa.Integer(), nullable=False),
    sa.Column('product_link', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['customer_link'], ['customer.id'], ),
    sa.ForeignKeyConstraint(['product_link'], ['product.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('order',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('quantity', sa.Integer(), nullable=False),
    sa.Column('price', sa.Float(), nullable=False),
    sa.Column('status', sa.String(length=100), nullable=False),
    sa.Column('payment_id', sa.String(length=1000), nullable=False),
    sa.Column('customer_link', sa.Integer(), nullable=False),
    sa.Column('product_link', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['customer_link'], ['customer.id'], ),
    sa.ForeignKeyConstraint(['product_link'], ['product.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('stock_history',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('product_id', sa.Integer(), nullable=False),
    sa.Column('previous_stock', sa.Integer(), nullable=False),
    sa.Column('new_stock', sa.Integer(), nullable=False),
    sa.Column('change', sa.Integer(), nullable=False),
    sa.Column('date_updated', sa.DateTime(), nullable=True),
    sa.Column('warehouse_location', sa.String(length=100), nullable=False),
    sa.Column('updated_by', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['product_id'], ['product.id'], ),
    sa.ForeignKeyConstraint(['updated_by'], ['customer.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('stock_history')
    op.drop_table('order')
    op.drop_table('cart')
    op.drop_table('product')
    op.drop_table('sub_category')
    op.drop_table('customer')
    op.drop_table('category')
    # ### end Alembic commands ###