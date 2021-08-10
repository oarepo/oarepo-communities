# -*- coding: utf-8 -*-
#
# Copyright (C) 2021 CESNET.
#
# OARepo-Communities is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.

"""OArepo module that adds support for communities"""

import os

from setuptools import find_packages, setup

readme = open('README.md').read()
history = open('CHANGES.rst').read()

OAREPO_VERSION = os.environ.get('OAREPO_VERSION', '3.3.0')

tests_require = [
    'pydocstyle',
    'isort'
]

extras_require = {
    'tests': [
        'oarepo[tests]~={version}'.format(version=OAREPO_VERSION),
        *tests_require
    ],
    'build': [
         'oarepo-model-builder'
    ]
}

extras_require['all'] = []
for reqs in extras_require.values():
    extras_require['all'].extend(reqs)

setup_requires = [
]

install_requires = [
    'oarepo-fsm>=1.6.1',
    'oarepo-micro-api',
    'oarepo-enrollment-permissions',
    'oarepo-ui',
    'oarepo-search',
    'boltons'
]

packages = find_packages(exclude=["tests", 'tests.api', 'tests.api.mappings', 'tests.api.mappings.v7'])

# Get the version string. Cannot be done with import!
g = {}
with open(os.path.join('oarepo_communities', 'version.py'), 'rt') as fp:
    exec(fp.read(), g)
    version = g['__version__']

setup(
    name='oarepo-communities',
    version=version,
    description=__doc__,
    long_description=readme + '\n\n' + history,
    keywords='invenio oarepo communities',
    long_description_content_type='text/markdown',
    license='MIT',
    author='Miroslav Bauer',
    author_email='bauer@cesnet.cz',
    url='https://github.com/oarepo/oarepo-communities',
    packages=packages,
    zip_safe=False,
    include_package_data=True,
    platforms='any',
    entry_points={
        'flask.commands': [
            'oarepo:communities = oarepo_communities.cli:communities',
        ],
        'invenio_base.apps': [
            'oarepo_communities = oarepo_communities:OARepoCommunities',
        ],
        # 'invenio_admin.actions': [],
        'invenio_access.system_roles': [
            'community_record_owner = oarepo_communities.permissions:community_record_owner',
        ],
        # 'invenio_assets.bundles': [],
        'invenio_base.api_apps': [
            'oarepo_communities = oarepo_communities:OARepoCommunities',
        ],
        'invenio_base.api_blueprints': [
            'oarepo_communities = oarepo_communities.views:blueprint',
        ],
        # 'invenio_base.blueprints': [],
        # 'invenio_celery.tasks': [],
        # 'invenio_db.models': [],
        'invenio_db.models': [
            'oarepo_communities = oarepo_communities.models',
        ],
        'invenio_db.alembic': [
            'oarepo_communities = oarepo_communities:alembic',
        ],
        'invenio_base.api_converters': [
            'commpid = oarepo_communities.converters:CommunityPIDConverter',
        ],
        'invenio_base.converters': [
            'commpid = oarepo_communities.converters:CommunityPIDConverter',
        ],
        'oarepo_mapping_includes': [
            'oarepo_communities = oarepo_communities.included_mappings'
        ],
        'invenio_jsonschemas.schemas': [
            'oarepo_communities = oarepo_communities.jsonschemas',
        ],
        'oarepo_model_builder.datamodels': [
            'oarepo_communities = oarepo_communities.datamodels'
        ]
        # 'invenio_pidstore.minters': [],
        # 'invenio_records.jsonresolver': [],
    },
    extras_require=extras_require,
    install_requires=install_requires,
    setup_requires=setup_requires,
    tests_require=tests_require,
    classifiers=[
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Development Status :: 1 - Planning',
    ],
)
