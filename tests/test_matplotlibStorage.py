# This file is part of obs_test.
#
# Developed for the LSST Data Management System.
# This product includes software developed by the LSST Project
# (http://www.lsst.org).
# See the COPYRIGHT file at the top-level directory of this distribution
# for details of code ownership.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#

import os
import tempfile
import unittest

# we only import lsst.obs.test.TestMapper from lsst.obs.test, but use the namespace to hide it from pytest
import lsst.obs.test
import lsst.utils.tests
from lsst.utils import getPackageDir
from lsst.daf.persistence import Butler
import shutil


ROOT = getPackageDir('obs_test')


class MatplotlibStorageTestCase(lsst.utils.tests.TestCase):

    def setUp(self):
        inputDir = os.path.join(ROOT, "data", "input")
        self.testDir = tempfile.mkdtemp(dir=os.path.join(ROOT, 'tests'), prefix=type(self).__name__+'-')
        self.butler = Butler(inputs=inputDir, outputs={"root": self.testDir, "mode": 'rw'})

    def tearDown(self):
        del self.butler
        if os.path.exists(self.testDir):
            shutil.rmtree(self.testDir)

    def testWriteFigure(self):
        import matplotlib
        matplotlib.use("Agg")
        from matplotlib import pyplot
        fig = pyplot.figure()
        pyplot.plot([0, 1], [0, 1], "k")
        self.butler.put(fig, "test_plot", visit=1, filter="g")
        self.assertTrue(self.butler.datasetExists("test_plot", visit=1, filter="g"))
        self.assertTrue(os.path.exists(self.butler.getUri("test_plot", visit=1, filter="g")))


class MemoryTester(lsst.utils.tests.MemoryTestCase):
    pass


def setup_module(module):
    lsst.utils.tests.init()


if __name__ == "__main__":
    lsst.utils.tests.init()
    unittest.main()
