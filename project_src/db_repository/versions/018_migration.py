from sqlalchemy import *
from migrate import *


from migrate.changeset import schema
pre_meta = MetaData()
post_meta = MetaData()
migration_tmp = Table('migration_tmp', pre_meta,
    Column('id', INTEGER, primary_key=True, nullable=False),
    Column('nickname', VARCHAR(length=64)),
    Column('email', VARCHAR(length=120)),
    Column('cellphone', VARCHAR(length=30)),
    Column('about_me', VARCHAR(length=140)),
    Column('last_seen', DATETIME),
    Column('password', VARCHAR(length=30)),
    Column('active', BOOLEAN),
    Column('confirmed_at', DATETIME),
    Column('org_id', INTEGER),
    Column('expert_id', INTEGER),
    Column('professional_id', INTEGER),
)

user = Table('user', pre_meta,
    Column('id', INTEGER, primary_key=True, nullable=False),
    Column('nickname', VARCHAR(length=64)),
    Column('email', VARCHAR(length=120)),
    Column('cellphone', VARCHAR(length=30)),
    Column('about_me', VARCHAR(length=140)),
    Column('last_seen', DATETIME),
    Column('password', VARCHAR(length=30)),
    Column('active', BOOLEAN),
    Column('confirmed_at', DATETIME),
    Column('org_id', INTEGER),
    Column('datatype_id', INTEGER),
    Column('expert_id', INTEGER),
    Column('kind_id', INTEGER),
    Column('subject_id', INTEGER),
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
    pre_meta.tables['migration_tmp'].drop()
    pre_meta.tables['user'].columns['datatype_id'].drop()
    pre_meta.tables['user'].columns['kind_id'].drop()
    pre_meta.tables['user'].columns['subject_id'].drop()
    post_meta.tables['user'].columns['professional_id'].create()


def downgrade(migrate_engine):
    # Operations to reverse the above upgrade go here.
    pre_meta.bind = migrate_engine
    post_meta.bind = migrate_engine
    pre_meta.tables['migration_tmp'].create()
    pre_meta.tables['user'].columns['datatype_id'].create()
    pre_meta.tables['user'].columns['kind_id'].create()
    pre_meta.tables['user'].columns['subject_id'].create()
    post_meta.tables['user'].columns['professional_id'].drop()
