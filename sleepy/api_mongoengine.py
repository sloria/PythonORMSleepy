#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''Hello Mongoengine.'''
from datetime import datetime, timedelta

from flask import Flask, jsonify, request, render_template, abort
from flask.ext.classy import FlaskView
from flask.ext.mongoengine import MongoEngine
from marshmallow import fields, Serializer
import mongoengine as mdb


class Settings:
    MONGODB_SETTINGS = {
        "DB": "inventory",
    }
    DEBUG = True

app = Flask(__name__)
app.config.from_object(Settings)

### Models ###

db = MongoEngine(app)

class Item(db.Document):
    name = mdb.StringField(max_length=100, required=True)
    checked_out = mdb.BooleanField(default=False)
    updated = mdb.DateTimeField(default=datetime.utcnow)

    def __repr__(self):
        return '<Item {0!r}>'.format(self.name)


class Person(db.Document):
    firstname = mdb.StringField(max_length=80, required=True)
    lastname = mdb.StringField(max_length=80, required=True)
    created = mdb.DateTimeField(default=datetime.utcnow)
    # Denormalize the items collection because there are no joins in MongoDB
    items = mdb.ListField(mdb.ReferenceField(Item))

    def __repr__(self):
        return "<Person '{0} {1}'>".format(self.firstname, self.lastname)

def get_item_person(item):
    '''Get an item's parent person.'''
    return Person.objects(items__in=[item]).first()

### Custom Serializers ###

class PersonDocSerializer(Serializer):
    id = fields.String()
    name = fields.Function(lambda p: "{0}, {1}".format(p['lastname'], p['firstname']))
    created = fields.DateTime()
    n_items = fields.Function(lambda p: len(p['items']))

class ItemDocSerializer(Serializer):
    id = fields.String()
    person = fields.Method("get_person")
    class Meta:
        additional = ('name', 'checked_out', 'updated')

    def get_person(self, item):
        person = Person.objects(items__in=[item['id']]).first()
        return PersonDocSerializer(person._data).data

### API ###

class ItemsView(FlaskView):
    route_base = '/items/'

    def index(self):
        '''Get all items.'''
        all_items = Item.objects.order_by("-updated")
        # Serializer takes data dict for each item
        item_data = [item._data for item in all_items]
        data = ItemDocSerializer(item_data).data
        return jsonify({"items": data})

    def get(self, id):
        '''Get an item.'''
        try:
            item = Item.objects.get(id=id)
        except mdb.ValidationError:  # Invalid ID
            abort(404)
        if not item:
            abort(404)
        return jsonify(ItemDocSerializer(item._data).data)

    def post(self):
        '''Insert a new item.'''
        data = request.json
        name = data.get("name", None)
        if not name:
            abort(400)
        item = Item(name=name)
        item.save()
        person_id = data.get("person_id")
        if person_id:
            person = Person.objects(id=person_id).first()
            if not person:
                abort(404)
            # Add item to person's items list
            person.items.append(item)
            person.save()
        return jsonify({"message": "Successfully added new item",
                        "item": ItemDocSerializer(item._data).data}), 201

    def delete(self, id):
        '''Delete an item.'''
        item = Item.objects(id=id).first()
        if not item:
            abort(404)
        item.delete()
        return jsonify({"message": "Successfully deleted item.",
                        "id": str(item.id)}), 200

    def put(self, id):
        '''Update an item.'''
        item = Item.objects(id=id).first()
        if not item:
            abort(404)
        # Update item
        item.name = request.json.get("name", item.name)
        item.checked_out = request.json.get("checked_out", item.checked_out)
        if request.json.get("person_id"):
            # remove the item from its person's items list and add it to the
            # new person's items list
            old_person = get_item_person(item)
            old_person.items.remove(item)
            old_person.save()
            person = Person.objects(id=str(request.json['person_id'])).first()
            if person:
                person.items.append(item)
            person.save()
        item.updated = datetime.utcnow()
        item.save()
        return jsonify({"message": "Successfully updated item.",
                        "item": ItemDocSerializer(item._data).data})


class PeopleView(FlaskView):
    route_base = '/people/'

    def index(self):
        '''Get all people, ordered by creation date.'''
        all_people = Person.objects.order_by("-created")
        people_data = [p._data for p in all_people]
        data = PersonDocSerializer(people_data).data
        return jsonify({"people": data})

    def get(self, id):
        '''Get a person.'''
        try:
            person = Person.objects.get(id=str(id))
        except mdb.ValidationError:
            abort(404)
        if not person:
            abort(404)
        return jsonify(PersonDocSerializer(person._data).data)

    def post(self):
        '''Insert a new person.'''
        data = request.json
        firstname = data.get("firstname")
        lastname = data.get("lastname")
        if not firstname or not lastname:
            abort(400)
        person = Person(firstname=firstname, lastname=lastname)
        person.save()
        return jsonify({"message": "Successfully added new person.",
                        "person": PersonDocSerializer(person._data).data}), 201

    def delete(self, id):
        '''Delete a person.'''
        person = Person.objects.get(id=id)
        if not person:
            abort(404)
        pid = person.id
        person.delete()
        return jsonify({"message": "Successfully deleted person.",
                        "id": str(pid)}), 200

class RecentCheckoutsView(FlaskView):
    '''Demonstrates a more complex query.'''

    route_base = '/recentcheckouts/'

    def index(self):
        '''Return items checked out in the past hour.'''
        hour_ago  = datetime.utcnow() - timedelta(hours=1)
        recent = Item.objects(checked_out=True, updated__gt=hour_ago)\
                                .order_by("-updated")
        recent_data = [i._data for i in recent]
        serialized = ItemDocSerializer(recent_data)
        return jsonify({"items": serialized.data})

@app.route("/")
def home():
    return render_template('index.html', orm="Mongoengine")

def drop_collections():
    Person.drop_collection()
    Item.drop_collection()

# Register views
api_prefix = "/api/v1/"
ItemsView.register(app, route_prefix=api_prefix)
PeopleView.register(app, route_prefix=api_prefix)
RecentCheckoutsView.register(app, route_prefix=api_prefix)

if __name__ == '__main__':
    app.run(port=5000)
