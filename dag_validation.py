import unittest
from airflow.models import DagBag

class TestDagIntegrity(unittest.TestCase):
    LOAD_SECOND_THRESHOLD = 2
    def setUp(self):
        self.dagbag = DagBag(dag_folder="{{dags}}", include_examples=False)
    def test_import_dags(self):
        self.assertFalse(
            len(self.dagbag.import_errors),
            'DAG import failures. Errors: {}'.format(
                self.dagbag.import_errors
            )
        )


suite = unittest.TestLoader().loadTestsFromTestCase(TestDagIntegrity)
unittest.TextTestRunner(verbosity=2).run(suite)
