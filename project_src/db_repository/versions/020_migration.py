from sqlalchemy import *
from migrate import *


from migrate.changeset import schema
pre_meta = MetaData()
post_meta = MetaData()
following_datasets = Table('following_datasets', post_meta,
    Column('dataset_udi', String),
    Column('follower_id', Integer),
)

user = Table('user', post_meta,
    Column('id', Integer, primary_key=True, nullable=False),
    Column('nickname', String(length=64)),
    Column('email', String(length=120)),
    Column('cellphone', String(length=30)),
    Column('password', String(length=30)),
    Column('about_me', String(length=140)),
    Column('last_seen', DateTime),
    Column('active', Boolean, default=ColumnDefault(True)),
    Column('confirmed_at', DateTime),
    Column('org_id', Integer),
    Column('expert_id', Integer),
    Column('professional_id', Integer),
)


def upgrade(migrate_engine):
    # Upgrade operations go here. Don't create your own engine; bind
    # migrate_engine to your metadata
    pre_meta.bind = migrate_engine
    post_meta.bind = migrate_engine
    post_meta.tables['following_datasets'].create()
    post_meta.tables['user'].columns['expert_id'].create()
    post_meta.tables['user'].columns['professional_id'].create()


def downgrade(migrate_engine):
    # Operations to reverse the above upgrade go here.
    pre_meta.bind = migrate_engine
    post_meta.bind = migrate_engine
    post_meta.tables['following_datasets'].drop()
    post_meta.tables['user'].columns['expert_id'].drop()
    post_meta.tables['user'].columns['professional_id'].drop()
