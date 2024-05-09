install:
	.venv/bin/pip install -r requirements.txt

pull:
	.venv/bin/python pull.py

sync:
	.venv/bin/python sync.py

visited:
	.venv/bin/python visited.py

map:
	.venv/bin/python map.py

requirements:
	.venv/bin/pip freeze > requirements.txt
