from mesa import Agent, Model
from mesa.space import Grid
from mesa.time import RandomActivation
from mesa.visualization.modules import CanvasGrid
from mesa.visualization.ModularVisualization import ModularServer

from pathfinding.core.diagonal_movement import DiagonalMovement
from pathfinding.core.grid import Grid as GridPath
from pathfinding.finder.a_star import AStarFinder

class WallBlock(Agent):
    def __init__(self, model, pos):
        super().__init__(model.next_id(), model)
        self.pos = pos
    def step(self):
        pass
class Caja(Agent):
    def __init__(self, model, pos):
        super().__init__(model.next_id(), model)
        self.pos = pos
        self.inStack = False
class Robot(Agent):
    def __init__(self, model, pos):
        super().__init__(model.next_id(), model)
        self.pos = pos
        self.model = model
        self.matrix = self.model.matrix
        grid = GridPath(matrix = self.matrix)
        self.grid = grid

    def step(self):
        
        minPath = 100
        self.grid.cleanup()
        grid = GridPath(matrix= self.matrix)
        self.grid = grid
        start = self.grid.node(self.pos[0], self.pos[1])
        allBoxesinStack = bool(self.model.initialBoxesPos)
        if allBoxesinStack:
            cajacerca = self.pos
        else:
            cajacerca = (1,1)
        finder = AStarFinder(diagonal_movement = DiagonalMovement.never)
        print("---------------- CAJAS Y DISTANCIA ------------------")
        for boxPos in self.model.initialBoxesPos.keys():
            self.grid.cleanup()
            grid = GridPath(matrix= self.matrix)
            self.grid = grid
            endTemp = self.grid.node(boxPos[0], boxPos[1])
            pathTemp, runsTemp = finder.find_path(start, endTemp, self.grid)
            print (boxPos, " -> ",len(pathTemp))
            if minPath > len(pathTemp):
                cajacerca = boxPos
                minPath = len(pathTemp)
        
        print ("----------CAJA MAS CERCANA ----------")
        print(cajacerca)
        self.grid.cleanup()
        grid = GridPath(matrix= self.matrix)
        self.grid = grid
        end = self.grid.node(cajacerca[0], cajacerca[1])
        path, runs = finder.find_path(start, end, self.grid)
        print ("----------CAMINO MAS CERCANA ----------")
        print (self.pos," -> ",path)
        if(len(path) > 1):
            next_move = path[1]
            if next_move in self.model.initialBoxesPos.keys():
                self.model.boxesFound.append(self.model.initialBoxesPos[next_move])
                self.model.initialBoxesPos.pop(next_move)
            
            self.model.grid.move_agent(self, next_move)



class Maze(Model):
    def __init__(self, amountOfAgents, amountOfBoxes):
        super().__init__()
        self.schedule = RandomActivation(self)
        self.grid = Grid(10, 10, torus=False)
        self.amountOfAgents = amountOfAgents
        self.amountOfBoxes = amountOfBoxes
        self.initialBoxesPos = {}
        self.boxesFound = []
        self.matrix = [
            [0,0,0,0,0,0,0,0,0,0],
            [0,1,1,1,0,0,1,1,1,0],
            [0,1,1,1,1,1,1,1,1,0],
            [0,1,1,1,1,1,1,1,1,0],
            [0,1,1,1,1,1,1,1,1,0],
            [0,1,1,1,1,1,1,1,1,0],
            [0,1,1,1,1,1,1,1,1,0],
            [0,1,1,1,1,1,1,1,1,0],
            [0,1,1,1,1,1,1,1,1,0],
            [0,0,0,0,0,0,0,0,0,0]
        ]
        for _,x,y in self.grid.coord_iter():
            if self.matrix[y][x] == 0:
                block = WallBlock(self, (x, y))
                self.grid.place_agent(block, block.pos)
                self.schedule.add(block)


        for i in range(self.amountOfBoxes):
            x = self.random.randint(2,8)
            y = self.random.randint(2,8)
            caja = Caja(self, (x,y))
            self.grid.place_agent(caja, (y,x))
            self.schedule.add(caja)
            self.initialBoxesPos[(y,x)] = caja

        for i in range(self.amountOfAgents):
            x = self.random.randint(2,8)
            y = self.random.randint(2,8)
            bender = Robot(self, (y,x))
            self.grid.place_agent(bender, (y,x))
            self.schedule.add(bender)


    def step(self):
        self.schedule.step()
        print(self.boxesFound)
        for boxToMove in self.boxesFound:
            self.grid.remove_agent(boxToMove)
            self.boxesFound.remove(boxToMove)

def agent_portrayal(agent):
    if type(agent) is Robot:
        return {"Shape": "robot.png", "Layer": 0}
    elif type(agent) is Caja:
        return {"Shape": "caja.png", "Layer": 0}
    else:
        return {"Shape": "rect", "w": 1, "h": 1, "Filled": "true", "Color": "Gray", "Layer": 0}

grid = CanvasGrid(agent_portrayal, 10, 10, 450, 450)

server = ModularServer(Maze, [grid], "Act_Integradora_A01733984", {'amountOfAgents':4, 'amountOfBoxes': 10})
server.port = 8522
server.launch()