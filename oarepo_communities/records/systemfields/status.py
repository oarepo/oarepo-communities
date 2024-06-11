from invenio_records.systemfields.base import SystemField


class RecordStatusField(SystemField):
    def __init__(self, key="status", initial="draft"):
        self._initial = initial
        super().__init__(key=key)

    def pre_commit(self, record):
        self.set_dictkey(record, self._get_cache(record))

    def post_init(self, record, data, model=None, **kwargs):
        if not self._get_cache(record) and "status" in record:
            self._set_cache(record, record["status"])

    def post_create(self, record):
        self._set_cache(record, self._initial)

    def __get__(self, record, owner=None):
        """Get the persistent identifier."""
        if record is None:
            return self
        return self._get_cache(record)

    def __set__(self, record, value):
        self._set_cache(record, value)
