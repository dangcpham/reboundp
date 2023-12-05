import unittest
import reboundp
import threading, time

class TestFeaturesPort(unittest.TestCase):
    def test_features_port(self):
        rebp = reboundp.ReboundParallel(lambda: 1)
        self.assertEqual(rebp.features, ["port"])
    
    def test_features_base_check_feature(self):
        def test_sim():
            time.sleep(1)

        rebp = reboundp.ReboundParallel(test_sim)
        threading.Timer(0.5, rebp.check_port_feature).start()
        rebp.run(jobs=10)

if __name__ == "__main__":
    unittest.main()