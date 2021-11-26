import flask
from flask.json import jsonify
import uuid
import roboCajas
from roboCajas import Maze, Robot

games = {}

app = flask.Flask(__name__)

@app.route("/games", methods=["POST"])

def create():
    global games
    id = str(uuid.uuid4())
    games[id] = Maze()
    return "ok", 201, {'Location': f"/games/{id}"}


@app.route("/games/<id>", methods=["GET"])
def queryState(id):
    global model
    model = games[id]
    model.step()
    listaRobots = []
    #buscar todos los agentes del modelo y si son cajas o robots incluirlos en el arreglo de diccionarios a mandar al json
    for i in range(len(model.schedule.agents)):
        ghost = model.schedule.agents[i]
        if type(ghost) is roboCajas.Robot:
            listaRobots.append({"x": ghost.pos[0], "y": ghost.pos[1], "tipo" : "Robot", "inStack" : 0, "inRobot" : False})
        elif type(ghost) is roboCajas.Caja:
            listaRobots.append({"x": ghost.pos[0], "y": ghost.pos[1], "tipo" : "Caja", "inStack" : ghost.inStack , "inRobot" : ghost.inRobot})
        else:
            i = i - 1
    return jsonify({"Items":listaRobots})

app.run()