import unittest
import reboundp
import threading, time

class TestFeaturesBase(unittest.TestCase):
    def test_features_base(self):
        rebp = reboundp.ReboundParallel(lambda: 1)
        self.assertEqual(rebp.features, [])
    
    def test_features_port_check_feature(self):
        def test_sim():
            time.sleep(1)

        rebp = reboundp.ReboundParallel(test_sim)
        def check_and_assert():
            with self.assertRaises(ImportError):
                rebp.check_port_feature()

        threading.Timer(0.5, check_and_assert).start()
        rebp.init_run(jobs=10)
        rebp.run()

if __name__ == "__main__":
    unittest.main()