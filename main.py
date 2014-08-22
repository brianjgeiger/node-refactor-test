# todo: warn on no default, or something
# todo: get default collection name for picklestorage, mongostorage constructors
# todo: requirements.txt
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

    def setup(self):
        self.category = "folder"
        self.save()


class Dashboard(Folder):

    find_query = Q('category', 'eq', 'dashboard')

    def setup(self):
        self.category = 'dashboard'
        existing_dashboards = Dashboard.find()
        if existing_dashboards.count() == 0:
            self.save()
        else:
            raise DashboardError("Two Dashboards")

    def look_at_me(self):
        return 'Look at me! I am', self.name, '!'


class Project(Node):

    find_query = Q('category', 'eq', 'project')

    def setup(self):
        self.category = "project"
        self.save()


class Data(Node):
    find_query = Q('category', 'eq', 'data')

    def setup(self):
        self.category = "data"
        self.save()


class Analysis(Node):
    find_query = Q('category', 'eq', 'analysis')

    def setup(self):
        self.category = "analysis"
        self.save()


class TestNodeRefactoring(unittest.TestCase):
    def setUp(self):
        client = MongoClient()
        db = client['node-refactor-db']

        db.node.remove()
        Node.set_storage(storage.MongoStorage(db, 'node'))

        folder = Folder(name="New Folder")
        folder.setup()
        dashboard = Dashboard(name="Dashboard")
        dashboard.setup()


        project = Project(name="Smarty")
        project.setup()
        project_two = Project(name="Test Project")
        project_two.setup()
        data = Data(name="My Cool Data")
        data.setup()
        data_two = Data(name="My Raw Data", number=31)
        data_two.setup()
        analysis = Analysis()
        analysis.setup()

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
        self.assertEqual(dashboard_excitement, ('Look at me! I am', 'Dashboard', '!'))

    def test_folder_cannot_use_dashboard_functionality(self):
        try:
            a_folder = Folder.find_one(Q('category', 'eq', 'dashboard'))
            try:
                a_folder.look_at_me()
                self.assertTrue(False)
            except AttributeError as e:
                self.assertTrue(True)
        except NoResultsFound as e:
                # Shouldn't get here because dashboards are folders
                self.assertTrue(False)

    def test_finding_incompatible_class(self):
        try:
            a_datum = Data.find_one(Q('category', 'eq', 'dashboard'))
            try:
                a_datum.look_at_me()
                self.assertTrue(False)
            except AttributeError as e:
                # Shouldn't get here because find_one should error out
                self.assertTrue(False)
        except NoResultsFound as e:
            self.assertTrue(True)

if __name__ == '__main__':
    unittest.main()