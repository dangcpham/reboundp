coverage erase

pip uninstall --y urllib3 rebound
coverage run -m -a unittest test_environment/test_features_base.py -v

pip install urllib3 rebound
coverage run -m -a unittest discover -s . -v
coverage run -m -a unittest test_environment/test_features_port.py -v

coverage html -d coverage_report