'''Serializers common to all apps.'''

from marshmallow import Serializer, fields


class PersonSerializer(Serializer):
    id = fields.Integer()
    name = fields.Function(lambda p: "{0}, {1}".format(p.lastname, p.firstname))
    created = fields.DateTime()
    n_items = fields.Integer()


class ItemSerializer(Serializer):
    person = fields.Nested(PersonSerializer, only=('id', 'name'), allow_null=True)

    class Meta:
        additional = ('id', 'name', 'checked_out', 'updated')
