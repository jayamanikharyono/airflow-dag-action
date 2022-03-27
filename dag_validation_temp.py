# -*- coding: utf-8 -*-
"""
@author: jayaharyonomanik
"""

import os
import logging
import unittest
from airflow.models import DagBag


class TestDagIntegrity(unittest.TestCase):
    LOAD_SECOND_THRESHOLD = 2

    def setUp(self):
        DAGS_DIR = os.getenv('INPUT_DAGPATHS')
        os.environ['PYTHONPATH'] = f"{os.getenv('PYTHONPATH')}:{DAGS_DIR}"
        logging.info("DAGs dir : {}".format(DAGS_DIR))
        self.dagbag = DagBag(dag_folder = DAGS_DIR, include_examples = False)

    def test_import_dags(self):
        self.assertFalse(
            len(self.dagbag.import_errors),
            'DAG import failures. Errors: {}'.format(
                self.dagbag.import_errors
            )
        )

    def tearDown(self):
        logging.info(self.dagbag.dagbag_report())


suite = unittest.TestLoader().loadTestsFromTestCase(TestDagIntegrity)
