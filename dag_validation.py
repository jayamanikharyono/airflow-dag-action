import os
import logging
import unittest
from airflow.models import DagBag


class TestDagIntegrity(unittest.TestCase):
    LOAD_SECOND_THRESHOLD = 2
    def setUp(self):
        DAGS_DIR = os.getenv('AIRFLOW_HOME')
        logging.info("DAGs dir : {}".format(DAGS_DIR))
        self.dagbag = DagBag(dag_folder = DAGS_DIR, include_examples = False)
    def test_import_dags(self):
        self.assertFalse(
            len(self.dagbag.import_errors),
            'DAG import failures. Errors: {}'.format(
                self.dagbag.import_errors
            )
        )


suite = unittest.TestLoader().loadTestsFromTestCase(TestDagIntegrity)
unittest.TextTestRunner(verbosity=2).run(suite)
