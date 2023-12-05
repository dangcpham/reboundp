pip uninstall --y urllib3 rebound
python -m unittest test_environment/test_features_base.py -v

pip install urllib3 rebound
python -m unittest discover -s . -v
python -m unittest test_environment/test_features_port.py -v