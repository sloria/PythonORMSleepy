#!/usr/bin/env python
# -*- coding: utf-8 -*-
import unittest
from nose.tools import *  # PEP8 asserts
from flask.ext.testing import TestCase

from sleepy.api_pony import Person, Item, app, db
from sleepy.serializers import ItemSerializer
from pony import orm


class TestPonyAPI(TestCase):
    TESTING = True
    DEBUG = True

    def create_app(self):
        app.config.from_object(self)
        return app

    def setUp(self):
        # create some items
        with orm.db_session:
            self.person = Person(firstname="Steve", lastname="Loria")
            self.person2 = Person(firstname="Monty", lastname="Python")
            self.item = Item(name="Foo")
            self.item2 = Item(name="Bar")

    def tearDown(self):
        db.drop_all_tables(with_all_data=True)
        db.disconnect()

    @orm.db_session
    def test_get_items(self):
        url = "/api/v1/items/"
        res = self.client.get(url)
        data = res.json
        assert_equal(res.status_code, 200)
        assert_equal(len(data['items']), 2)
        assert_equal(data['items'][0]['name'], self.item2.name)

    # def test_get_item(self):
    #     url = '/api/v1/items/{0}'.format(self.item.id)
    #     res = self.client.get(url)
    #     data = res.json
    #     assert_equal(res.status_code, 200)
    #     assert_equal(data['name'], self.item.name)
    #     assert_equal(data['person']['id'], self.person.id)

    # def test_get_persons(self):
    #     res = self.client.get('/api/v1/people/')
    #     assert_equal(res.status_code, 200)
    #     assert_equal(len(res.json['people']), 2)
    #     assert_equal(res.json['people'][0]['name'],
    #                 "{0}, {1}".format(self.person2.lastname, self.person2.firstname))

    # def test_get_person(self):
    #     res = self.client.get('/api/v1/people/{0}'.format(self.person.id))
    #     assert_equal(res.status_code, 200)
    #     assert_equal(res.json['name'], "{0}, {1}".format(self.person.lastname,
    #                                                     self.person.firstname))
    #     assert_equal(res.json['n_items'], 1)


    # def test_get_nonexistent_person(self):
    #     res = self.client.get("/api/v1/people/10")
    #     assert_equal(res.status_code, 404)

    # def _post_json(self, url, data):
    #     return self.client.post(url,
    #                             data=json.dumps(data),
    #                             content_type='application/json')

    # def _put_json(self, url, data):
    #     return self.client.put(url,
    #                             data=json.dumps(data),
    #                             content_type='application/json')

    # def test_post_item(self):
    #     res = self._post_json("/api/v1/items/", {"name": "Ipad"})
    #     assert_equal(res.status_code, 201)
    #     item = Item.query.all()[-1]
    #     assert_true(item is not None)
    #     assert_equal(item.name, "Ipad")

    # def test_post_item_with_person_id(self):
    #     res = self._post_json('/api/v1/items/',
    #                           {"name": "Ipod", "person_id": self.person.id})
    #     assert_equal(res.status_code, 201)
    #     item = Item.query.all()[-1]
    #     assert_equal(item.person, self.person)

    # def test_post_person(self):
    #     res = self._post_json('/api/v1/people/',
    #                         {'firstname': 'Steven', 'lastname': 'Loria'})
    #     assert_equal(res.status_code, 201)
    #     person = Person.query.all()[-1]
    #     assert_equal(person.firstname, "Steven")
    #     assert_equal(person.lastname, "Loria")

    # def test_delete_item(self):
    #     assert_in(self.item, Item.query.all())
    #     res = self.client.delete("/api/v1/items/{0}".format(self.item.id))
    #     assert_not_in(self.item, Item.query.all())

    # def test_put_item(self):
    #     res = self._put_json("/api/v1/items/{0}".format(self.item.id),
    #                         {"checked_out": True,
    #                         "person_id": self.person2.id})
    #     assert_true(self.item.checked_out)
    #     assert_equal(self.item.person, self.person2)

    # def test_delete_person(self):
    #     all_persons = Person.query.all()
    #     assert_in(self.person, all_persons)
    #     self.client.delete('/api/v1/people/{0}'.format(self.person.id))
    #     all_persons = Person.query.all()
    #     assert_not_in(self.person, all_persons)

    # def test_recent(self):
    #     self.item.checked_out = True
    #     self.item2.checked_out = False
    #     db.session.add_all([self.item, self.item2])
    #     db.session.commit()
    #     res = self.client.get("/api/v1/recentcheckouts/")
    #     assert_in(ItemSerializer(self.item).data, res.json['items'])
    #     assert_not_in(ItemSerializer(self.item2).data, res.json['items'])


if __name__ == '__main__':
    unittest.main()
