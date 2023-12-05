import unittest
import numpy as np
from reboundp import utils

class TestUtils(unittest.TestCase):
    def test_dim(self):
        a = [1,2]
        self.assertEqual(utils.dim(a), [2])
        self.assertEqual(len(utils.dim(a)), 1)
        
        a = [[1,2], [2,3]]
        self.assertEqual(utils.dim(a), [2,2])
        self.assertEqual(len(utils.dim(a)), 2)
    
    def test_islist(self):
        a = [1,2]
        self.assertTrue(utils.is_list(a))

        a = np.asarray([1,2,3])
        self.assertTrue(utils.is_list(a))

        a = "Not a list"
        self.assertTrue(not utils.is_list(a))

        a = {"a": "b"}
        self.assertTrue(not utils.is_list(a))

        a = (1,2,3)
        self.assertTrue(not utils.is_list(a))

        a = 0
        self.assertTrue(not utils.is_list(a))

        a = 1.234
        self.assertTrue(not utils.is_list(a))
        
        class WeirdType():
            def __init__(self):
                pass
        
        a = WeirdType()
        self.assertTrue(not utils.is_list(a))

    def test_timeformat(self):
        self.assertEqual(utils.time_format(0.1),  "0.10s")
        self.assertEqual(utils.time_format(61),   "01m01s")
        self.assertEqual(utils.time_format(3661), "01h01m01s")
        self.assertEqual(utils.time_format(3661), "01h01m01s")
        self.assertEqual(utils.time_format(3600*24 + 3661), "1days 01h01m01s")

if __name__ == "__main__":
    unittest.main()