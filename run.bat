@REM gunicorn -w 4 -b 0.0.0.0:8850 app:app

waitress-serve --host=127.0.0.1 --port=8850 --threads=6 app:app