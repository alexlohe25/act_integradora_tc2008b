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
        self.inStack = False
    def step(self):
        pass

class Caja(Agent):
    def __init__(self, model, pos):
        super().__init__(model.next_id(), model)
        self.pos = pos
    def step(self):
        pass
class Robot(Agent):
    def __init__(self, model, pos):
        super().__init__(model.next_id(), model)
        self.pos = pos
        self.model = model
        self.matrix = self.model.matrix
        grid = GridPath(matrix = self.matrix)
        self.grid = grid
    def step(self):
        self.grid.cleanup()
        grid = GridPath(matrix= self.matrix)
        self.grid = grid
        start = self.grid.node(self.pos[0], self.pos[1])
        end = self.grid.node(8,8)
        finder = AStarFinder(diagonal_movement = DiagonalMovement.never)
        path, runs = finder.find_path(start, end, self.grid)
        if(len(path) > 1):
            self.model.grid.move_agent(self, path[1])



class Maze(Model):
    def __init__(self, amountOfAgents, amountOfBoxes):
        super().__init__()
        self.schedule = RandomActivation(self)
        self.grid = Grid(10, 10, torus=False)
        self.amountOfAgents = amountOfAgents
        self.amountOfBoxes = amountOfBoxes
        self.initialBoxesPos = []
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
            caja = Caja(self, (y,x))
            self.grid.place_agent(caja, caja.pos)
            self.schedule.add(caja)
            self.initialBoxesPos.append(caja.pos)

        for i in range(self.amountOfAgents):
            x = self.random.randint(2,8)
            y = self.random.randint(2,8)
            bender = Robot(self, (y,x))
            self.grid.place_agent(bender, bender.pos)
            self.schedule.add(bender)


    def step(self):
        self.schedule.step()

def agent_portrayal(agent):
    if type(agent) is Robot:
        return {"Shape": "robot.png", "Layer": 0}
    elif type(agent) is Caja:
        return {"Shape": "caja.png", "Layer": 0}
    else:
        return {"Shape": "rect", "w": 1, "h": 1, "Filled": "true", "Color": "Gray", "Layer": 0}

grid = CanvasGrid(agent_portrayal, 10, 10, 450, 450)

server = ModularServer(Maze, [grid], "Act_Integradora_A01733984", {'amountOfAgents':5, 'amountOfBoxes': 14})
server.port = 8522
server.launch()