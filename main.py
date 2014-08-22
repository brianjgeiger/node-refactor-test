import unittest
from modularodm import StoredObject
from modularodm import fields
from modularodm import storage
from pymongo import MongoClient
from modularodm.validators import *
from modularodm.query.querydialect import DefaultQueryDialect as Q
from modularodm.exceptions import NoResultsFound


class DashboardError(Exception):

    def __init__(self, value):
        self.value = value

    def __str__(self):
        return repr(self.value)


def filter_none(*items):
    return [item for item in items if item is not None]


def join_queries(*queries):
    try:
        return_value = reduce(
            lambda x, y: x & y,
            filter_none(*queries),
        )
    except TypeError:
        return_value = None
    return return_value


class Node(StoredObject):
    _id = fields.StringField(primary=True, default=lambda: str(ObjectId()))
    category = fields.StringField(default="node")
    name = fields.StringField(default="")
    number = fields.IntegerField(default=1)
    _meta = {
        'abstract': True,
    }

    find_query = None

    @classmethod
    def find_one(cls, query=None, **kwargs):
        query = join_queries(query, cls.find_query)
        return super(Node, cls).find_one(query=query, **kwargs)


    @classmethod
    def find(cls, query=None, **kwargs):
        query = join_queries(query, cls.find_query)
        return super(Node, cls).find(query=query, **kwargs)


class Folder(Node):
    find_query = Q('category', 'eq', 'folder') | Q('category', 'eq', 'dashboard')

    def __init__(self, **kwargs):
        super(Node, self).__init__(**kwargs)
        self.category = "folder"

    def be_a_folder(self):
        return 'I am a folder.'


class Dashboard(Folder):
    find_query = Q('category', 'eq', 'dashboard')

    def __init__(self, **kwargs):
        existing_dashboards = Dashboard.find()
        if existing_dashboards.count() != 0:
            raise DashboardError("Two Dashboards")
        super(Node, self).__init__(**kwargs)
        self.category = 'dashboard'

    def look_at_me(self):
        return 'Look at me! I am', self.name, '!'


class Project(Node):
    find_query = Q('category', 'eq', 'project')

    def __init__(self, **kwargs):
        super(Node, self).__init__(**kwargs)
        self.category = "project"


class Data(Node):
    find_query = Q('category', 'eq', 'data')

    def __init__(self, **kwargs):
        super(Node, self).__init__(**kwargs)
        self.category = "data"


class Analysis(Node):
    find_query = Q('category', 'eq', 'analysis')

    def __init__(self, **kwargs):
        super(Node, self).__init__(**kwargs)
        self.category = "analysis"


class TestNodeRefactoring(unittest.TestCase):

    def setUp(self):
        client = MongoClient()
        db = client['node-refactor-db']

        db.node.remove()
        Node.set_storage(storage.MongoStorage(db, 'node'))

        Folder(name="New Folder").save()
        Dashboard(name="Dashboard").save()
        Project(name="Smarty").save()
        Project(name="Test Project").save()
        Data(name="My Cool Data").save()
        Data(name="My Raw Data", number=31).save()
        Analysis().save()

    def test_project_count(self):
        self.assertEqual(Node.find().count(), 7)
        self.assertEqual(Folder.find().count(), 2)
        self.assertEqual(Dashboard.find().count(), 1)
        self.assertEqual(Project.find().count(), 2)
        self.assertEqual(Data.find().count(), 2)
        self.assertEqual(Analysis.find().count(), 1)

    def test_only_one_dashboard(self):
        # Should only be able to have one Dashboard
        with self.assertRaises(DashboardError):
            Dashboard(name="Second Dashboard").setup()

    def test_dashboard_only_functionality(self):
        a_dashboard = Dashboard.find_one(Q('name', 'eq', 'Dashboard'))
        dashboard_excitement = a_dashboard.look_at_me()
        self.assertEqual(dashboard_excitement, ('Look at me! I am', 'Dashboard', '!'),
                         'Did not get proper return value from Dashboard() method.')

    def test_folder_uses_folder_methods(self):
        some_folders = Folder.find()
        a_folder = some_folders[0]
        folder_response = a_folder.be_a_folder()
        self.assertEqual(folder_response, 'I am a folder.', 'Folder not using folder method.')

    def test_dashboard_uses_folder_methods(self):
        a_dashboard = Dashboard.find_one()
        folder_response = a_dashboard.be_a_folder()
        self.assertEqual(folder_response, 'I am a folder.', 'Dashboard not using folder method.')

    def test_analysis_does_not_use_folder_methods(self):
        analysis = Analysis.find_one()
        with self.assertRaises(AttributeError):
            analysis.be_a_folder()

    def test_folder_cannot_use_dashboard_functionality(self):
        # Folder class should not be able to use a Dashboard method
        a_folder = Folder.find_one(Q('category', 'eq', 'dashboard'))
        with self.assertRaises(AttributeError):
            a_folder.look_at_me()

    def test_finding_incompatible_class(self):
        # Data class should not be able to find a dashboard object
        with self.assertRaises(NoResultsFound):
            Data.find_one(Q('category', 'eq', 'dashboard'))

    def test_subclasses_should_set_data_on_creation(self):
        data = Data.find_one(Q('name', 'eq', 'My Raw Data'))
        self.assertEqual(data.number, 31, 'Number was not properly stored during object creation.')

    def test_subclasses_that_do_not_set_data_should_get_defaults(self):
        analysis = Analysis.find_one()
        self.assertEqual(analysis.number, 1, 'Default number was not saved on this object.')


class TestUtilityFunctions(unittest.TestCase):
    def test_filter_none(self):
        empty_list = filter_none(None, None, None)
        self.assertEqual(empty_list, [])
        a_list = filter_none('a', None)
        self.assertEqual(a_list, ['a'])
        no_list = filter_none()
        self.assertEqual(no_list, [])

if __name__ == '__main__':
    unittest.main()