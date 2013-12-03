#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''Hello Pony.'''
from datetime import datetime, timedelta

from flask import Flask, jsonify, request, render_template, abort
from flask.ext.classy import FlaskView
from pony import orm

from serializers import ItemSerializer, PersonSerializer


class Settings:
    DB_PROVIDER = "sqlite"
    DB_NAME = "inventory.db"
    DEBUG = True

app = Flask(__name__)
app.config.from_object(Settings)

### Models ###

db = orm.Database('sqlite', 'inventory.db', create_db=True)


class Person(db.Entity):
    _table_ = 'people'
    firstname = orm.Required(unicode, 80, nullable=False)
    lastname = orm.Required(unicode, 80, nullable=False)
    created = orm.Required(datetime, default=datetime.utcnow)
    items = orm.Set("Item")

    @property
    def n_items(self):
        return orm.count(item for item in self.items)

    def __repr__(self):
        return "<Person '{0} {1}'>".format(self.firstname, self.lastname)


class Item(db.Entity):
    _table_ = 'items'
    name = orm.Required(unicode, 100, nullable=False)
    person = orm.Optional(Person)
    checked_out = orm.Required(bool, default=False)
    updated = orm.Required(datetime, default=datetime.utcnow)

    def __repr__(self):
        return '<Item {0!r}>'.format(self.name)


### API ###

class ItemsView(FlaskView):
    route_base = '/items/'

    def index(self):
        '''Get all items.'''
        all_items = orm.select(item for item in Item)\
                                .order_by(orm.desc(Item.updated))[:]
        data = ItemSerializer(all_items).data
        return jsonify({"items": data})

    def get(self, id):
        '''Get an item.'''
        try:
            item = Item[id]
        except orm.ObjectNotFound:
            abort(404)
        return jsonify(ItemSerializer(item).data)

    def post(self):
        '''Insert a new item.'''
        data = request.json
        name = data.get("name", None)
        if not name:
            abort(400)
        pid = data.get("person_id")
        if pid:
            person = Person.get(id=pid)  # None if not found
        else:
            person = None
        item = Item(name=name, person=person)
        orm.commit()
        return jsonify({"message": "Successfully added new item",
                        "item": ItemSerializer(item).data}), 201

    def delete(self, id):
        '''Delete an item.'''
        try:
            item = Item[id]
        except orm.ObjectNotFound:
            abort(404)
        item.delete()
        orm.commit()
        return jsonify({"message": "Successfully deleted item.",
                        "id": id}), 200

    def put(self, id):
        '''Update an item.'''
        try:
            item = Item[id]
        except orm.ObjectNotFound:
            abort(404)
        # Update item
        item.name = request.json.get("name", item.name)
        item.checked_out = request.json.get("checked_out", item.checked_out)
        pid = request.json.get("person_id")
        if pid:
            person = Person.get(id=pid)
            item.person = person or item.person
        else:
            item.person = None
        item.updated = datetime.utcnow()
        orm.commit()
        return jsonify({"message": "Successfully updated item.",
                        "item": ItemSerializer(item).data})

class PeopleView(FlaskView):
    route_base = '/people/'

    def index(self):
        '''Get all people, ordered by creation date.'''
        all_people = orm.select(p for p in Person).order_by(orm.desc(Person.created))[:]
        data = PersonSerializer(all_people, exclude=('created',)).data
        return jsonify({"people": data})

    def get(self, id):
        '''Get a person.'''
        try:
            person = Person[id]
        except orm.ObjectNotFound:
            abort(404)
        return jsonify(PersonSerializer(person).data)

    def post(self):
        '''Insert a new person.'''
        data = request.json
        firstname = data.get("firstname")
        lastname = data.get("lastname")
        if not firstname or not lastname:
            abort(400)  # Must specify both first and last name
        person = Person(firstname=firstname, lastname=lastname)
        orm.commit()
        return jsonify({"message": "Successfully added new person.",
                        "person": PersonSerializer(person).data}), 201

    def delete(self, id):
        '''Delete a person.'''
        try:
            person = Person[id]
        except orm.ObjectNotFound:
            abort(404)
        person.delete()
        orm.commit()
        return jsonify({"message": "Successfully deleted person.",
                        "id": id}), 200

class RecentCheckoutsView(FlaskView):
    '''Demonstrates a more complex query.'''
    route_base = '/recentcheckouts/'

    def index(self):
        '''Return items checked out in the past hour.'''
        hour_ago  = datetime.utcnow() - timedelta(hours=1)
        recent = orm.select(item for item in Item
                                if item.checked_out and
                                    item.updated > hour_ago)[:]
        return jsonify({"items": ItemSerializer(recent).data})

@app.route("/")
def home():
    return render_template('index.html', orm="Pony ORM")

# Generate object-database mapping
db.generate_mapping(check_tables=False)

# Register views
api_prefix = "/api/v1/"
ItemsView.register(app, route_prefix=api_prefix)
PeopleView.register(app, route_prefix=api_prefix)
RecentCheckoutsView.register(app, route_prefix=api_prefix)


if __name__ == '__main__':
    db.create_tables()
    # Make sure each thread gets a db session
    app.wsgi_app = orm.db_session(app.wsgi_app)
    app.run(port=5000)
