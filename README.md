# Python ORM/ODM Examples, For The Sleepy

The same RESTful API (an inventory app), implemented using different ORM/ODMs--a sort of "Hello World" tour of Python data mapper libraries.

Each example demonstrates the syntax for declaring models as well as basic querying, inserting, updating, and deleting of records.


## Featuring. . .

**[SQLAlchemy](http://www.sqlalchemy.org/)** (Relational DBs)

[Full Example](https://github.com/sloria/PythonORMSleepy/blob/master/sleepy/api_sqlalchemy.py)

```python
hour_ago  = datetime.utcnow() - timedelta(hours=1)
recent_items = Item.query.filter(Item.checked_out &
                                (Item.updated > hour_ago)) \
                                .order_by(Item.updated.desc()).all()
```

**[Peewee](http://peewee.readthedocs.org/en/latest/)** (Relational DBs)

[Full Example](https://github.com/sloria/PythonORMSleepy/blob/master/sleepy/api_peewee.py)

```python
hour_ago  = datetime.utcnow() - timedelta(hours=1)
recent_items =Item.select().where(Item.checked_out &
                                (Item.updated > hour_ago)) \
                                .order_by(Item.updated.desc())
```

**[Mongoengine](http://mongoengine.org)** (MongoDB)

[Full Example](https://github.com/sloria/PythonORMSleepy/blob/master/sleepy/api_mongoengine.py)

```python
hour_ago  = datetime.utcnow() - timedelta(hours=1)
recent_items = Item.objects(checked_out=True, updated__gt=hour_ago)\
                            .order_by("-updated")
```

**[Stdnet](http://pythonhosted.org/python-stdnet/index.html)** (Redis)

[Full Example](https://github.com/sloria/PythonORMSleepy/blob/master/sleepy/api_stdnet.py)

```python
hour_ago  = datetime.utcnow() - timedelta(hours=1)
recent_items = models.item.filter(checked_out=True, updated__gt=hour_ago)\
                                .sort_by("-updated").all()
```

**[Pony](http://ponyorm.com/)** (Relational DBs)

[Full Example](https://github.com/sloria/PythonORMSleepy/blob/master/sleepy/api_pony.py)

```python
hour_ago  = datetime.utcnow() - timedelta(hours=1)
recent_items = orm.select(item for item in Item
                                if item.checked_out and
                                    item.updated > hour_ago)\
                                    .order_by(Item.updated.desc())[:]
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

## "Why isn't  _____ included here?"

To which I respond: Why don't you [fork](https://github.com/sloria/PythonORMSleepy/fork) this project?



## License 

[MIT Licensed](http://sloria.mit-license.org/).
