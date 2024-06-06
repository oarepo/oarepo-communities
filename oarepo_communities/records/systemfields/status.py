from invenio_records.systemfields.base import SystemField


class RecordStatusField(SystemField):
    def __init__(self, key="status", initial="draft"):
        self._status = initial
        super().__init__(key=key)

    def pre_commit(self, record):
        self.set_dictkey(record, self._status)

    def __get__(self, record, owner=None):
        """Get the persistent identifier."""
        if record is None:
            return self
        return self._status

    def __set__(self, record, value):
        self._status = value
