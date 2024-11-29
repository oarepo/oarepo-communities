import json

import pytest


@pytest.fixture
def sample_record_with_community_data(communities):
    community_aaa = str(communities['aaa'].id)
    community_bbb = str(communities['bbb'].id)
    return {
        'parent': {
            'communities': {
                'ids': {
                    community_aaa, community_bbb
                },
                'default': community_aaa
            }
        }
    }


@pytest.fixture
def as_comparable_dict():
    def _as_comparable(d):
        if isinstance(d, dict):
            return {k: _as_comparable(v) for k, v in sorted(d.items())}
        if isinstance(d, (list, tuple)):
            return set(_as_comparable(v) for v in d)
        return d

    return _as_comparable