'''Serializers common to all apps.'''

from marshmallow import Serializer, fields


class PersonSerializer(Serializer):
    id = fields.Integer()
    name = fields.Function(lambda p: "{0}, {1}".format(p.lastname, p.firstname))
    created = fields.DateTime()
    n_items = fields.Method("get_n_items")

    def get_n_items(self, person):
        # Need list comp to ensure that query is executed in Peewee
        return len([item for item in person.items])


class ItemSerializer(Serializer):
    person = fields.Nested(PersonSerializer, only=('id', 'name'), allow_null=True)
    class Meta:
        additional = ('id', 'name', 'checked_out', 'updated')
