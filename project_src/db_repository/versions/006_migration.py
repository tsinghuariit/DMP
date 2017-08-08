from sqlalchemy import *
from migrate import *


from migrate.changeset import schema
pre_meta = MetaData()
post_meta = MetaData()
category = Table('category', post_meta,
    Column('id', Integer, primary_key=True, nullable=False),
    Column('name', String(length=60)),
    Column('description', String(length=560)),
    Column('sort', Integer),
    Column('is_custom', Integer),
    Column('parent_id', Integer),
    Column('type', Integer),
)


def upgrade(migrate_engine):
    # Upgrade operations go here. Don't create your own engine; bind
    # migrate_engine to your metadata
    pre_meta.bind = migrate_engine
    post_meta.bind = migrate_engine
    post_meta.tables['category'].columns['type'].create()


def downgrade(migrate_engine):
    # Operations to reverse the above upgrade go here.
    pre_meta.bind = migrate_engine
    post_meta.bind = migrate_engine
    post_meta.tables['category'].columns['type'].drop()
