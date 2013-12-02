#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''Hello SQLAlchemy.'''
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
    firstname = orm.Required(unicode, 80, nullable=False)
    lastname = orm.Required(unicode, 80, nullable=False)
    created = orm.Required(datetime, default=datetime.utcnow)
    # items = orm.Set("Item")

    @property
    def n_items(self):
        return orm.count(item for item in self.items)

    def __repr__(self):
        return "<Person '{0} {1}'>".format(self.firstname, self.lastname)

class Item(db.Entity):
    name = orm.Required(unicode, 100, nullable=False)
    # person = orm.Optional(Person)
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
        item = Item.query.get_or_404(int(id))
        return jsonify(ItemSerializer(item).data)

    def post(self):
        '''Insert a new item.'''
        data = request.json
        name = data.get("name", None)
        if not name:
            abort(400)
        person = Person.query.filter_by(id=data.get("person_id", None)).first()
        item = Item(name=name, person=person)
        db.session.add(item)
        db.session.commit()
        return jsonify({"message": "Successfully added new item",
                        "item": ItemSerializer(item).data}), 201

    def delete(self, id):
        '''Delete an item.'''
        item = Item.query.get_or_404(int(id))
        db.session.delete(item)
        db.session.commit()
        return jsonify({"message": "Successfully deleted item.",
                        "id": item.id}), 200

    def put(self, id):
        '''Update an item.'''
        item = Item.query.get_or_404(int(id))
        # Update item
        item.name = request.json.get("name", item.name)
        item.checked_out = request.json.get("checked_out", item.checked_out)
        if request.json.get("person_id"):
            person = Person.query.get(int(request.json['person_id']))
            item.person = person or item.person
        else:
            item.person = None
        item.updated = datetime.utcnow()
        db.session.add(item)
        db.session.commit()
        return jsonify({"message": "Successfully updated item.",
                        "item": ItemSerializer(item).data})

class PeopleView(FlaskView):
    route_base = '/people/'

    def index(self):
        '''Get all people, ordered by creation date.'''
        all_people = Person.query.order_by(Person.created.desc()).all()
        data = PersonSerializer(all_people, exclude=('created',)).data
        return jsonify({"people": data})

    def get(self, id):
        '''Get a person.'''
        person = Person.query.get_or_404(int(id))
        return jsonify(PersonSerializer(person).data)

    def post(self):
        '''Insert a new person.'''
        data = request.json
        firstname = data.get("firstname")
        lastname = data.get("lastname")
        if not firstname or not lastname:
            abort(400)  # Must specify both first and last name
        person = Person(firstname=firstname, lastname=lastname)
        db.session.add(person)
        db.session.commit()
        return jsonify({"message": "Successfully added new person.",
                        "person": PersonSerializer(person).data}), 201

    def delete(self, id):
        '''Delete a person.'''
        person = Person.query.get_or_404(int(id))
        db.session.delete(person)
        db.session.commit()
        return jsonify({"message": "Successfully deleted person.",
                        "id": person.id}), 200

class RecentCheckoutsView(FlaskView):
    '''Demonstrates a more complex query.'''
    route_base = '/recentcheckouts/'

    def index(self):
        '''Return items checked out in the past hour.'''
        hour_ago  = datetime.utcnow() - timedelta(hours=1)
        recent = Item.query.filter(Item.checked_out &
                                    (Item.updated > hour_ago)) \
                                    .order_by(Item.updated.desc()).all()
        return jsonify({"items": ItemSerializer(recent).data})

@app.route("/")
def home():
    return render_template('index.html', orm="SQLAlchemy")

# Generate object-database mapping
db.generate_mapping()

# Register views
api_prefix = "/api/v1/"
ItemsView.register(app, route_prefix=api_prefix)
PeopleView.register(app, route_prefix=api_prefix)
RecentCheckoutsView.register(app, route_prefix=api_prefix)


if __name__ == '__main__':
    db.create_tables()
    app.run(port=5000)
