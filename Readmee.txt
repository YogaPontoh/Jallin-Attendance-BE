# MAC OS
python3 -m venv .venv
. .venv/bin/activate

# Windows
py -m venv .venv
.venv\Scripts\Activate

*Normal Run
flask --app main run

*Debug Run
flask --app main --debug run

flask --app main run --debug --port 5001

flask --app main run --port 5001

pip install -r requirements.txt