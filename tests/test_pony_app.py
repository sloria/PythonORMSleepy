#!/usr/bin/env python
# -*- coding: utf-8 -*-
import unittest
from nose.tools import *  # PEP8 asserts
from flask.ext.testing import TestCase
from flask import json

from sleepy.api_pony import Person, Item, app, db
from sleepy.serializers import ItemSerializer
from pony import orm
from pony.orm import db_session


class TestPonyAPI(TestCase):
    '''WARNING: This test case drops all the tables in the dev db.'''

    TESTING = True
    DEBUG = True

    def create_app(self):
        app.config.from_object(self)
        return app

    def setUp(self):
        db.create_tables()
        # create some items
        with db_session:
            self.person = Person(firstname="Steve", lastname="Loria")
            self.person2 = Person(firstname="Monty", lastname="Python")
            self.item = Item(name="Foo", person=self.person)
            self.item2 = Item(name="Bar")

    def tearDown(self):
        db.drop_all_tables(with_all_data=True)

    @db_session
    def test_get_items(self):
        url = "/api/v1/items/"
        res = self.client.get(url)
        data = res.json
        item = Item[self.item2.id]
        assert_equal(res.status_code, 200)
        assert_equal(len(data['items']), 2)
        assert_equal(data['items'][0]['name'], item.name)

    @db_session
    def test_get_item(self):
        url = '/api/v1/items/{0}'.format(self.item.id)
        res = self.client.get(url)
        data = res.json
        item = Item[self.item.id]
        assert_equal(res.status_code, 200)
        assert_equal(data['name'], item.name)
        assert_equal(data['person']['id'], self.person.id)

    @db_session
    def test_get_persons(self):
        res = self.client.get('/api/v1/people/')
        person = Person[self.person2.id]
        assert_equal(res.status_code, 200)
        assert_equal(len(res.json['people']), 2)
        assert_equal(res.json['people'][0]['name'],
                    "{0}, {1}".format(person.lastname, person.firstname))

    @db_session
    def test_get_person(self):
        res = self.client.get('/api/v1/people/{0}'.format(self.person.id))
        assert_equal(res.status_code, 200)
        person = Person[self.person.id]
        assert_equal(res.json['name'], "{0}, {1}".format(person.lastname,
                                                        person.firstname))
        assert_equal(res.json['n_items'], 1)

    @db_session
    def test_get_nonexistent_person(self):
        res = self.client.get("/api/v1/people/10")
        assert_equal(res.status_code, 404)

    def _post_json(self, url, data):
        return self.client.post(url,
                                data=json.dumps(data),
                                content_type='application/json')

    def _put_json(self, url, data):
        return self.client.put(url,
                                data=json.dumps(data),
                                content_type='application/json')
    @db_session
    def test_post_item(self):
        res = self._post_json("/api/v1/items/", {"name": "Ipad"})
        assert_equal(res.status_code, 201)
        item = list(Item.select())[-1]
        assert_true(item is not None)
        assert_equal(item.name, "Ipad")

    @db_session
    def test_post_item_with_person_id(self):
        res = self._post_json('/api/v1/items/',
                              {"name": "Ipod", "person_id": self.person.id})
        assert_equal(res.status_code, 201)
        item = list(Item.select())[-1]
        person = Person[self.person.id]
        assert_equal(item.person, person)

    @db_session
    def test_post_person(self):
        res = self._post_json('/api/v1/people/',
                            {'firstname': 'Steven', 'lastname': 'Loria'})
        assert_equal(res.status_code, 201)
        person = list(Person.select())[-1]
        assert_equal(person.firstname, "Steven")
        assert_equal(person.lastname, "Loria")

    @db_session
    def test_delete_item(self):
        item = Item[self.item.id]
        assert_in(item, Item.select()[:])
        res = self.client.delete("/api/v1/items/{0}".format(self.item.id))
        assert_not_in(self.item, Item.select())

    @db_session
    def test_put_item(self):
        item = Item[self.item.id]
        person = Person[self.person2.id]
        res = self._put_json("/api/v1/items/{0}".format(item.id),
                            {"checked_out": True,
                            "person_id": self.person2.id})
        assert_true(item.checked_out)
        assert_equal(item.person, person)

    @db_session
    def test_delete_person(self):
        person = Person[self.person.id]
        assert_in(person, Person.select()[:])
        self.client.delete('/api/v1/people/{0}'.format(self.person.id))
        assert_not_in(person, Person.select()[:])

    @db_session
    def test_recent(self):
        item = Item[self.item.id]
        item2 = Item[self.item2.id]
        item.checked_out = True
        item2.checked_out = False
        orm.commit()
        res = self.client.get("/api/v1/recentcheckouts/")
        assert_in(ItemSerializer(item).data, res.json['items'])
        assert_not_in(ItemSerializer(item2).data, res.json['items'])


if __name__ == '__main__':
    unittest.main()
