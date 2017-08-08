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
)

dataset = Table('dataset', pre_meta,
    Column('udi', VARCHAR(length=140), primary_key=True, nullable=False),
    Column('title', VARCHAR(length=140)),
    Column('published', DATETIME),
    Column('updated', DATETIME),
    Column('datasource', VARCHAR(length=1024)),
    Column('author', INTEGER),
    Column('contact', VARCHAR(length=40)),
    Column('desc', VARCHAR(length=1024)),
    Column('authority', VARCHAR(length=40)),
    Column('kind', VARCHAR(length=40)),
    Column('expert', VARCHAR(length=40)),
    Column('subject', VARCHAR(length=40)),
    Column('datatype', VARCHAR(length=40)),
)

dataset = Table('dataset', post_meta,
    Column('udi', String(length=140), primary_key=True, nullable=False),
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
    post_meta.tables['category'].create()
    pre_meta.tables['dataset'].columns['author'].drop()
    pre_meta.tables['dataset'].columns['authority'].drop()
    pre_meta.tables['dataset'].columns['datatype'].drop()
    pre_meta.tables['dataset'].columns['expert'].drop()
    pre_meta.tables['dataset'].columns['kind'].drop()
    pre_meta.tables['dataset'].columns['subject'].drop()
    post_meta.tables['dataset'].columns['author_id'].create()
    post_meta.tables['dataset'].columns['authority_id'].create()
    post_meta.tables['dataset'].columns['datatype_id'].create()
    post_meta.tables['dataset'].columns['expert_id'].create()
    post_meta.tables['dataset'].columns['kind_id'].create()
    post_meta.tables['dataset'].columns['subject_id'].create()


def downgrade(migrate_engine):
    # Operations to reverse the above upgrade go here.
    pre_meta.bind = migrate_engine
    post_meta.bind = migrate_engine
    post_meta.tables['category'].drop()
    pre_meta.tables['dataset'].columns['author'].create()
    pre_meta.tables['dataset'].columns['authority'].create()
    pre_meta.tables['dataset'].columns['datatype'].create()
    pre_meta.tables['dataset'].columns['expert'].create()
    pre_meta.tables['dataset'].columns['kind'].create()
    pre_meta.tables['dataset'].columns['subject'].create()
    post_meta.tables['dataset'].columns['author_id'].drop()
    post_meta.tables['dataset'].columns['authority_id'].drop()
    post_meta.tables['dataset'].columns['datatype_id'].drop()
    post_meta.tables['dataset'].columns['expert_id'].drop()
    post_meta.tables['dataset'].columns['kind_id'].drop()
    post_meta.tables['dataset'].columns['subject_id'].drop()
