#!/usr/bin/env python
# -*- coding: utf-8 -*-
import unittest
import time
from nose.tools import *  # PEP8 asserts
from flask.ext.testing import TestCase
from flask import json
from stdnet import odm

from sleepy.api_stdnet import app, register_models
from sleepy.serializers import ItemSerializer

models = odm.Router('redis://localhost:6379')


class TestStdnetAPI(TestCase):
    TESTING = True
    DEBUG = True

    def create_app(self):
        app.config.from_object(self)
        register_models(models)
        return app

    def setUp(self):
        # create some items
        self.person = models.person.new(firstname="Steve", lastname="Loria")
        self.person2 = models.person.new(firstname="Monty", lastname="Python")
        self.item = models.item.new(name="Foo", person=self.person)
        self.item.save()
        self.person.save()
        self.item2 = models.item.new(name="Bar")
        self.person2.save()
        self.item2.save()

    def tearDown(self):
        models.flush()

    def test_get_items(self):
        url = "/api/v1/items/"
        res = self.client.get(url)
        data = res.json
        assert_equal(res.status_code, 200)
        assert_equal(len(data['items']), 2)
        assert_equal(data['items'][0]['name'], self.item2.name)

    def test_get_item(self):
        url = '/api/v1/items/{0}'.format(self.item.id)
        res = self.client.get(url)
        data = res.json
        assert_equal(res.status_code, 200)
        assert_equal(data['name'], self.item.name)
        assert_equal(data['person']['id'], self.person.id)

    def test_get_nonexistent_item(self):
        url = '/api/v1/items/{0}'.format("abc")
        res = self.client.get(url)
        assert_equal(res.status_code, 404)

    def test_get_persons(self):
        res = self.client.get('/api/v1/people/')
        assert_equal(res.status_code, 200)
        assert_equal(len(res.json['people']), models.person.query().count())

    def test_get_person(self):
        res = self.client.get('/api/v1/people/{0}'.format(self.person.id))
        assert_equal(res.status_code, 200)
        assert_equal(res.json['name'], "{0}, {1}".format(self.person.lastname,
                                                        self.person.firstname))
        assert_equal(res.json['n_items'], 1)


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

    def test_post_item(self):
        res = self._post_json("/api/v1/items/", {"name": "Ipad"})
        assert_equal(res.status_code, 201)
        item = models.item.query().sort_by("-updated")[0]
        assert_true(item is not None)
        assert_equal(item.name, "Ipad")

    def test_post_item_with_person_id(self):
        res = self._post_json('/api/v1/items/',
                              {"name": "Ipod", "person_id": str(self.person.id)})
        assert_equal(res.status_code, 201)
        item = models.item.query()[0]
        assert_equal(item.person, self.person)

    def test_post_person(self):
        res = self._post_json('/api/v1/people/',
                            {'firstname': 'Foo', 'lastname': 'Bar'})
        assert_equal(res.status_code, 201)
        person = models.person.query().sort_by("-created")[0]
        assert_equal(person.firstname, "Foo")
        assert_equal(person.lastname, "Bar")

    def test_delete_item(self):
        all_items = models.item.query()
        assert_in(self.item, all_items)
        res = self.client.delete("/api/v1/items/{0}".format(self.item.id))
        all_items = models.item.query()
        assert_not_in(self.item, all_items)

    def test_put_item(self):
        res = self._put_json("/api/v1/items/{0}".format(self.item.id),
                            {"checked_out": True,
                            "person_id": str(self.person2.id)})
        item = models.item.get(id=self.item.id)
        assert_true(item.checked_out)
        assert_equal(item.person, self.person2)

    def test_delete_person(self):
        all_persons = models.person.query()
        assert_in(self.person, all_persons)
        self.client.delete('/api/v1/people/{0}'.format(self.person.id))
        all_persons = models.person.query()
        assert_not_in(self.person, all_persons)

    def test_recent(self):
        self.item.checked_out = True
        self.item2.checked_out = False
        self.item.save()
        self.item2.save()
        res = self.client.get("/api/v1/recentcheckouts/")
        assert_in(ItemSerializer(self.item).data, res.json['items'])
        assert_not_in(ItemSerializer(self.item2).data, res.json['items'])


if __name__ == '__main__':
    unittest.main()
