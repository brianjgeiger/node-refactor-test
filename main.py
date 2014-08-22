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
        if query is None:
            if cls.find_query is None:
                return super(Node, cls).find_one(**kwargs)
            query = cls.find_query
        else:
            if cls.find_query is not None:
                query = cls.find_query & query

        return super(Node, cls).find_one(query=query, **kwargs)

    @classmethod
    def find(cls, query=None, **kwargs):
        if query is None:
            if cls.find_query is None:
                return super(Node, cls).find(**kwargs)
            query = cls.find_query
        else:
            if cls.find_query is not None:
                query = cls.find_query & query

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

        folder = Folder(name="New Folder")
        folder.save()
        dashboard = Dashboard(name="Dashboard")
        dashboard.save()

        project = Project(name="Smarty")
        project.save()
        project_two = Project(name="Test Project")
        project_two.save()

        data = Data(name="My Cool Data")
        data.save()
        data_two = Data(name="My Raw Data", number=31)
        data_two.save()

        analysis = Analysis()
        analysis.save()

    def test_project_count(self):
        all_nodes = Node.find()
        all_folders = Folder.find()
        all_dashboards = Dashboard.find()
        all_projects = Project.find()
        all_data = Data.find()
        all_analysis = Analysis.find()
        self.assertEqual(all_nodes.count(), 7)
        self.assertEqual(all_folders.count(), 2)
        self.assertEqual(all_dashboards.count(), 1)
        self.assertEqual(all_projects.count(), 2)
        self.assertEqual(all_data.count(), 2)
        self.assertEqual(all_analysis.count(), 1)

    def test_only_one_dashboard(self):
        try:
            dashboard_two = Dashboard(name="Second Dashboard")
            dashboard_two.setup()
            self.assertTrue(False)
        except DashboardError:
            self.assertTrue(True)

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

if __name__ == '__main__':
    unittest.main()