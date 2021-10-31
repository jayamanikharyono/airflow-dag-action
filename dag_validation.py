"""
@author: jayaharyonomanik
"""

import os
import logging
import unittest
from airflow.models import DagBag

logger = logging.getLogger()
logger.setLevel(logging.INFO)
logging.basicConfig(format='%(asctime)s %(message)s')


class TestDagIntegrity(unittest.TestCase):
    LOAD_SECOND_THRESHOLD = 2
    def setUp(self):
        DAGS_DIR = "/github/workspace/" + os.getenv('INPUT_DAGPATHS')
        logger.info("DAGs dir : {}".format(DAGS_DIR))
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