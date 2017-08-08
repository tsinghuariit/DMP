from sqlalchemy import *
from migrate import *


from migrate.changeset import schema
pre_meta = MetaData()
post_meta = MetaData()
dataset_history = Table('dataset_history', post_meta,
    Column('his_id', Integer, primary_key=True, nullable=False),
    Column('his_version', Integer),
    Column('his_created', DateTime),
    Column('udi', String(length=140)),
    Column('title', String(length=140)),
    Column('published', DateTime),
    Column('updated', DateTime),
    Column('datasource', String(length=1024)),
    Column('author_id', Integer),
    Column('contact', String(length=40)),
    Column('desc', String(length=1024)),
    Column('authority_id', Integer),
    Column('kind_id', Integer),
    Column('expert_id', Integer),
    Column('subject_id', Integer),
    Column('datatype_id', Integer),
)


def upgrade(migrate_engine):
    # Upgrade operations go here. Don't create your own engine; bind
    # migrate_engine to your metadata
    pre_meta.bind = migrate_engine
    post_meta.bind = migrate_engine
    post_meta.tables['dataset_history'].columns['his_created'].create()


def downgrade(migrate_engine):
    # Operations to reverse the above upgrade go here.
    pre_meta.bind = migrate_engine
    post_meta.bind = migrate_engine
    post_meta.tables['dataset_history'].columns['his_created'].drop()
