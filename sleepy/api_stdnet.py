#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''Hello Stdnet.'''
import logging
from datetime import datetime, timedelta

from flask import Flask, jsonify, request, render_template, abort
from flask.ext.classy import FlaskView
from stdnet import odm
from serializers import ItemSerializer, PersonSerializer


class Settings:
    REDIS_URL = 'redis://'
    DEBUG = True

app = Flask(__name__)
app.config.from_object(Settings)

### Models ###

models = odm.Router(app.config['REDIS_URL'])

class Person(odm.StdModel):
    firstname = odm.CharField(required=True)
    lastname = odm.CharField(required=True)
    created = odm.DateTimeField(default=datetime.utcnow)

    @property
    def n_items(self):
        return len(self.items.all())

    def __unicode__(self):
        return "<Person '{0} {1}'>".format(self.firstname, self.lastname)


class Item(odm.StdModel):
    name = odm.CharField(required=True)
    person = odm.ForeignKey(Person, related_name='items', required=False)
    checked_out = odm.BooleanField(default=False)
    updated = odm.DateTimeField(default=datetime.utcnow)

    def __unicode__(self):
        return '<Item {0!r}>'.format(self.name)


### API ###

class ItemsView(FlaskView):
    route_base = '/items/'

    def index(self):
        '''Get all items.'''
        all_items = models.item.query().sort_by("-updated").all()
        data = ItemSerializer(all_items).data
        return jsonify({"items": data})

    def get(self, id):
        '''Get an item.'''
        try:
            item = models.item.query().get(id=id)
        except Item.DoesNotExist:
            abort(404)
        return jsonify(ItemSerializer(item).data)

    def post(self):
        '''Insert a new item.'''
        data = request.json
        name = data.get("name", None)
        person_id = data.get("person_id")
        person = None
        checked_out = data.get("checked_out", False)
        if not name:
            abort(400)
        if person_id:
            try:
                person = models.person.query().get(id=person_id)
            except Person.DoesNotExist:
                pass
        item = models.item.new(name=name, person=person, checked_out=checked_out)
        return jsonify({"message": "Successfully added new item",
                        "item": ItemSerializer(item).data}), 201

    def delete(self, id):
        '''Delete an item.'''
        try:
            item = models.item.query().get(id=id)
        except Item.DoesNotExist:
            abort(404)
        item.delete()
        return jsonify({"message": "Successfully deleted item.",
                        "id": item.id}), 200

    def put(self, id):
        '''Update an item.'''
        try:
            item = models.item.query().get(id=int(id))
        except Item.DoesNotExist:
            abort(404)
        # Update item
        item.name = request.json.get("name", item.name)
        item.checked_out = request.json.get("checked_out", item.checked_out)
        if request.json.get("person_id"):
            try:
                person = models.person.get(id=int(request.json['person_id']))
            except Person.DoesNotExist:
                abort(404)
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
        all_people = models.person.query().sort_by("-created")
        data = PersonSerializer(all_people, exclude=('created',)).data
        return jsonify({"people": data})

    def get(self, id):
        '''Get a person.'''
        try:
            person = models.person.query().get(id=id)
        except Person.DoesNotExist:
            abort(404)
        return jsonify(PersonSerializer(person).data)

    def post(self):
        '''Insert a new person.'''
        data = request.json
        firstname = data.get("firstname")
        lastname = data.get("lastname")
        if not firstname or not lastname:
            abort(400)  # Must specify both first and last name
        person = models.person.new(firstname=firstname, lastname=lastname)
        person.save()
        return jsonify({"message": "Successfully added new person.",
                        "person": PersonSerializer(person).data}), 201

    def delete(self, id):
        '''Delete a person.'''
        try:
            person = models.person.query().get(id=id)
        except Person.DoesNotExist:
            abort(404)
        person.delete()
        return jsonify({"message": "Successfully deleted person.",
                        "id": person.id}), 200

class RecentCheckoutsView(FlaskView):
    '''Demonstrates a more complex query.'''
    route_base = '/recentcheckouts/'

    def index(self):
        '''Return items checked out in the past hour.'''
        hour_ago  = datetime.utcnow() - timedelta(hours=1)
        recent = models.item.filter(checked_out=True).sort_by("-updated").all()
        return jsonify({"items": ItemSerializer(recent).data})

@app.route("/")
def home():
    return render_template('index.html', orm="Stdnet")

def register_models(router):
    router.register(Item)
    router.register(Person)
    return router

# Register views
api_prefix = "/api/v1/"
ItemsView.register(app, route_prefix=api_prefix)
PeopleView.register(app, route_prefix=api_prefix)
RecentCheckoutsView.register(app, route_prefix=api_prefix)

# Register models
register_models(models)

if __name__ == '__main__':
    app.run(port=5000)
