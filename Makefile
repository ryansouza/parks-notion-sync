install:
	.venv/bin/pip install -r requirements.txt

pull:
	.venv/bin/python pull.py

requirements:
	.venv/bin/pip freeze > requirements.txt
