see [https://github.com/darlentar/rtaoai2] for the new version

# Installation
Tested with python3.12.
`python -m venv .venv`
`source .venv/bin/activate`
`pip install -r requirements.txt`
if you need to run tests:
`pip install -e rtaoai`
To run the server you need to define `OPENAI_API_KEY` env variable.
Run the backend dev server with `fastapi dev server.py`.
Just open the file `index.html` (test only with Chrome sadly).

# Quick manual
Click on `Record` to start to ask a question and `Stop Record` when you finish your question.
Some tested question:
 * what is the available stock for product 2
 * what is the most available stock for all product
 * list all stock available
 
# Todo
At the beginning I started the project with a bottom-up approach, but I don't find it nice for this exercice.
I switched to a top-down approach, which for me seems easier for this exercice. As such there is some useless
function (as `session_created_handler`).
Some function are not unit-tested as at the end I need a lot of prototyping to understand how certain the API works (especially audio pcm encoding with base64).
The UI need some quick QoL improvement (eg. stop the current audio).
All openai realtime API is not implemented, I just implemented what I need.
