pip uninstall --y urllib3 rebound
python -m unittest test_environment/test_features_base.py -v

pip install 'rebound<4.0.0'
python -m unittest test_environment/test_features_rebound3.py -v
pip uninstall --y rebound

pip install urllib3 'rebound>=4.0.0'
python -m unittest test_environment/test_features_port.py -v
python -m unittest discover -s . -v