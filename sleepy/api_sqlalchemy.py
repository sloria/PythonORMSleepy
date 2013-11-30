#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''Hello SQLAlchemy.'''
from datetime import datetime, timedelta

from flask import Flask, jsonify, request, render_template, abort
from flask.ext.sqlalchemy import SQLAlchemy
from flask.ext.classy import FlaskView

from serializers import ItemSerializer, PersonSerializer


class Settings:
    DB_NAME = "inventory.db"
    # Put the db file in project root
    SQLALCHEMY_DATABASE_URI = "sqlite:///{0}".format(DB_NAME)
    DEBUG = True

app = Flask(__name__)
app.config.from_object(Settings)

### Models ###

db = SQLAlchemy()
db.init_app(app)

class Person(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    firstname = db.Column(db.String(80), nullable=False)
    lastname = db.Column(db.String(80), nullable=False)
    created = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return "<Person '{0} {1}'>".format(self.firstname, self.lastname)

class Item(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    person_id = db.Column(db.Integer, db.ForeignKey('person.id'), nullable=True)
    person = db.relationship("Person", backref=db.backref("items"))
    checked_out = db.Column(db.Boolean, default=False)
    updated = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return '<Item {0!r}>'.format(self.name)


### API ###

class ItemsView(FlaskView):
    route_base = '/items/'

    def index(self):
        '''Get all items.'''
        all_items = Item.query.order_by(Item.updated.desc()).all()
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
        item = Item(name=data['name'], person=person)
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
        all_people = Person.query.order_by(Person.created.desc())
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

# Register views
api_prefix = "/api/v1/"
ItemsView.register(app, route_prefix=api_prefix)
PeopleView.register(app, route_prefix=api_prefix)
RecentCheckoutsView.register(app, route_prefix=api_prefix)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(port=5000)
