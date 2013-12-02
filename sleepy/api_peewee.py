#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''Hello Peewee.'''
from datetime import datetime, timedelta

from flask import Flask, jsonify, request, render_template, abort
from flask.ext.classy import FlaskView
from flask_peewee.db import Database
from flask_peewee.utils import get_object_or_404
import peewee as pw

from serializers import ItemSerializer, PersonSerializer


class Settings:
    DATABASE = {
        "name": "inventory.db",
        "engine": "peewee.SqliteDatabase"
    }
    DEBUG = True

app = Flask(__name__)
app.config.from_object(Settings)

### Models ###

db = Database(app)

class BaseModel(db.Model):
    def __marshallable__(self):
        '''Return marshallable dictionary for marshmallow support.'''
        return dict(self.__dict__)['_data']

class Person(BaseModel):
    firstname = pw.CharField(max_length=80, null=False)
    lastname = pw.CharField(max_length=80, null=False)
    created = pw.DateTimeField(default=datetime.utcnow)

    @property
    def n_items(self):
        return self.items.count()

    def __repr__(self):
        return "<Person '{0} {1}'>".format(self.firstname, self.lastname)

class Item(BaseModel):
    name = pw.CharField(max_length=100, null=False)
    person = pw.ForeignKeyField(Person, related_name="items", null=True)
    checked_out = pw.BooleanField(default=False)
    updated = pw.DateTimeField(default=datetime.utcnow)

    def __repr__(self):
        return '<Item {0!r}>'.format(self.name)


### API ###

class ItemsView(FlaskView):
    route_base = '/items/'

    def index(self):
        '''Get all items.'''
        all_items = Item.select().order_by(Item.updated.desc())
        data = ItemSerializer(all_items).data
        return jsonify({"items": data})

    def get(self, id):
        '''Get an item.'''
        # Could also use flask_peewee.utils.get_object_or_404
        try:
            item = Item.get(Item.id == id)
        except Item.DoesNotExist:
            abort(404)
        return jsonify(ItemSerializer(item).data)

    def post(self):
        '''Insert a new item.'''
        data = request.json
        name = data.get("name", None)
        if not name:
            abort(400)  # Must specify name
        person_id = data.get("person_id")
        if person_id:
            try:
                person = Person.get(Person.id == person_id)
            except Person.DoesNotExist:
                person = None
        else:
            person = None
        item = Item.create(name=name, person=person)
        return jsonify({"message": "Successfully added new item",
                        "item": ItemSerializer(item).data}), 201

    def delete(self, id):
        '''Delete an item.'''
        item = get_object_or_404(Item, Item.id == id)
        item.delete_instance()
        return jsonify({"message": "Successfully deleted item.",
                        "id": item.id}), 200

    def put(self, id):
        '''Update an item.'''
        item = get_object_or_404(Item, Item.id == id)
        # Update item
        item.name = request.json.get("name", item.name)
        item.checked_out = request.json.get("checked_out", item.checked_out)
        if request.json.get("person_id"):
            person = Person.get(Person.id == int(request.json['person_id']))
            item.person = person or item.person
        else:
            item.person = None
        item.updated = datetime.utcnow()
        item.save()
        return jsonify({"message": "Successfully updated item.",
                        "item": ItemSerializer(item).data})

class PeopleView(FlaskView):
    route_base = '/people/'

    def index(self):
        '''Get all people, ordered by creation date.'''
        all_items = Person.select().order_by(Person.created.desc())
        data = PersonSerializer(all_items, exclude=('created',)).data
        return jsonify({"people": data})

    def get(self, id):
        '''Get a person.'''
        # Could also use flask_peewee.utils.get_object_or_404
        try:
            person = Person.get(Person.id == int(id))
        except Person.DoesNotExist:
            abort(404)
        return jsonify(PersonSerializer(person).data)

    def post(self):
        '''Insert a new person.'''
        data = request.json
        firstname = data.get("firstname")
        lastname = data.get("lastname")
        if not firstname or not lastname:
            abort(400)  # Must specify first and last name
        person = Person(firstname=firstname, lastname=lastname)
        person.save()
        return jsonify({"message": "Successfully added new person.",
                        "person": PersonSerializer(person).data}), 201

    def delete(self, id):
        '''Delete a person.'''
        person = get_object_or_404(Person, Person.id == int(id))
        pid = person.id
        person.delete_instance()
        return jsonify({"message": "Successfully deleted person.",
                        "id": pid}), 200

class RecentCheckoutsView(FlaskView):
    '''Demonstrates a more complex query.'''

    route_base = '/recentcheckouts/'

    def index(self):
        '''Return items checked out in the past hour.'''
        hour_ago  = datetime.utcnow() - timedelta(hours=1)
        query = Item.select().where(Item.checked_out &
                                    (Item.updated > hour_ago)) \
                                    .order_by(Item.updated.desc())
        recent = [item for item in query]  # Executes query
        return jsonify({"items": ItemSerializer(recent).data})

@app.route("/")
def home():
    return render_template('index.html', orm="Peewee")

def create_tables():
    Person.create_table(True)
    Item.create_table(True)

def drop_tables():
    Person.drop_table(True)
    Item.drop_table(True)

# Register views
api_prefix = "/api/v1/"
ItemsView.register(app, route_prefix=api_prefix)
PeopleView.register(app, route_prefix=api_prefix)
RecentCheckoutsView.register(app, route_prefix=api_prefix)

if __name__ == '__main__':
    create_tables()
    app.run(port=5000)
