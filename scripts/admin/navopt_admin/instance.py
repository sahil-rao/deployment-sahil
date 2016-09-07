from .table import format_table
import operator


DEFAULT_FIELDS = (
    'instance_id',
    'name',
    'service',
    'service_type',
    'state',
    'private_ip_address',
)
DEFAULT_SORT_FIELDS = 'name'


class Instance(object):
    def __init__(self, instance):
        self._instance = instance
        self._tags = {}

    def __getattr__(self, key):
        return getattr(self._instance, key)

    @property
    def state(self):
        return self._instance.state['Name']

    @property
    def name(self):
        return self.tag('Name')

    @property
    def service(self):
        if not hasattr(self, '_service'):
            self._service = self.tag('Service')

            # FIXME: Work around old-style instances.
            if self._service is None:
                self._service = self.name

        return self._service

    @property
    def service_type(self):
        if not hasattr(self, '_service_type'):
            self._service_type = self.tag('Type')

            # FIXME: Work around old-style instances.
            if self._service_type is None and self.name is not None:
                name = self.name.lower()
                if 'mongo' in name:
                    self._service_type = 'mongo'
                elif 'elasticsearch' in name:
                    self._service_type = 'elasticsearch'
                elif 'redis' in name:
                    self._service_type = 'redis'

        return self._service_type

    def tag(self, name):
        try:
            value = self._tags[name]
        except KeyError:
            value = None

            for tag in self.tags or ():
                if tag['Key'] == name:
                    value = tag['Value']

            self._tags[name] = value

        return value

    def get_field(self, key):
        try:
            return getattr(self, key)
        except AttributeError:
            pass

        tag_key = key.lower()

        for tag in self._instance.tags:
            if tag['Key'].lower() == tag_key:
                return tag['Value']

        return None

    def __str__(self):
        return str(self._instance)


def format_instances(instances,
                     fields=None,
                     sort_field=None,
                     show_header=True):
    if fields is None:
        fields = DEFAULT_FIELDS

    if sort_field is None:
        sort_field = DEFAULT_SORT_FIELDS

    return format_table(instances,
                        fields=fields,
                        key=operator.attrgetter,
                        sort_field=sort_field,
                        show_header=show_header)
