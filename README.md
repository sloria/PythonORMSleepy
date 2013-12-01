# Python ORM/ODM Examples, For The Sleepy

The same RESTful API (an inventory app), implemented using different ORM/ODMs, i.e. a sort of "Hello World" tour of Python data mapper libraries.

Each example demonstrates the syntax for declaring models as well as basic querying, inserting, updating, and deleting of records.


## Featuring. . .

**[SQLAlchemy](http://www.sqlalchemy.org/)** (Relational DBs)

```python
hour_ago  = datetime.utcnow() - timedelta(hours=1)
recent_items = Item.query.filter(Item.checked_out &
                                (Item.updated > hour_ago)) \
                                .order_by(Item.updated.desc()).all()
```

**[Peewee](http://peewee.readthedocs.org/en/latest/)** (Relational DBs)

```python
hour_ago  = datetime.utcnow() - timedelta(hours=1)
recent_items =Item.select().where(Item.checked_out &
                                (Item.updated > hour_ago)) \
                                .order_by(Item.updated.desc())
```

**[Mongoengine](http://mongoengine.org)** (MongoDB)

```python
hour_ago  = datetime.utcnow() - timedelta(hours=1)
recent_items = Item.objects(checked_out=True, updated__gt=hour_ago)\
                            .order_by("-updated")
```

**[Stdnet](http://pythonhosted.org/python-stdnet/index.html)** (Redis)

```python
hour_ago  = datetime.utcnow() - timedelta(hours=1)
recent_items = models.item.filter(checked_out=True, updated__gt=hour_ago)\
                                .sort_by("-updated").all()
```

. . . and more to come.

Each of these was put to REST by [Flask](http://flask.pocoo.org), [Flask-Classy](http://pythonhosted.org/Flask-Classy/), and [marshmallow](http://marshmallow.readthedocs.org).

## Running an example

First, install dependencies.

    $ pip install -r requirements.txt

Then run the example of your choice.

    $ python sleepy/api_sqlalchemy.py

## Browser interface
An interactive browser interface is included to test out the REST API.

<img src="https://dl.dropboxusercontent.com/u/1693233/github/inventory-api.png" alt="Browser interface">

To use the browser interface, run an example and browse to `http://localhost:5000`.

## License 

[MIT Licensed](http://sloria.mit-license.org/).
