from mesa import Agent, Model
from mesa.space import Grid, MultiGrid
from mesa.time import RandomActivation
from mesa.visualization.modules import CanvasGrid
from mesa.visualization.ModularVisualization import ModularServer

from pathfinding.core.diagonal_movement import DiagonalMovement
from pathfinding.core.grid import Grid as GridPath
from pathfinding.finder.a_star import AStarFinder

import sys
#agente para delimitar los muros
class WallBlock(Agent):
    def __init__(self, model, pos):
        super().__init__(model.next_id(), model)
        self.pos = pos
    def step(self):
        pass
#agente que funge como pila de cajas, su principal atributo es el contador
class Stack(Agent):
    def __init__(self, model, pos):
        super().__init__(model.next_id(), model)
        self.pos = pos
        self.model = model
        self.boxCounter = 0
    def step(self):
        pass
#agente Caja, que tiene 2 flags para indicar si se encuentra en una pila de altura n o si la caja está recogida por un Robot
class Caja(Agent):
    def __init__(self, model, pos):
        super().__init__(model.next_id(), model)
        self.pos = pos
        self.inStack = 1
        self.inRobot = False
#agente Robot, que posee 2 movimientos principales: ir a buscar una caja y dejar dicha caja en una pila
class Robot(Agent):
    def __init__(self, model, pos):
        super().__init__(model.next_id(), model)
        self.pos = pos
        self.model = model
        self.gotBox = False
        self.matrix = self.model.matrix
        grid = GridPath(matrix = self.matrix)
        self.grid = grid

    def step(self):
        #si no tiene una caja por llevar, la busca
        if not self.gotBox:
            self.collectBox()
        else:
            #si la tiene, la dejará en la pila más cercana que tenga menos de 5 cajas apiladas
            self.leaveBox()

    #metodo que aplica el algoritmo AStar a todas las cajas en posiciones iniciales
    def collectBox(self):
        #inicializadores del AStar
        minPath = 100
        self.grid.cleanup()
        grid = GridPath(matrix= self.matrix)
        self.grid = grid
        start = self.grid.node(self.pos[0], self.pos[1])
        allBoxesinStack = bool(self.model.initialBoxesPos)
        finder = AStarFinder(diagonal_movement = DiagonalMovement.never)
        #si todavia hay cajas por acomodar, busca la caja mas cercana por el AStar comparando tamaño del arreglo de pasos
        if allBoxesinStack:
            cajacerca = self.pos
            for boxPos in self.model.initialBoxesPos.keys():
                self.grid.cleanup()
                grid = GridPath(matrix= self.matrix)
                self.grid = grid
                endTemp = self.grid.node(boxPos[0], boxPos[1])
                pathTemp, runsTemp = finder.find_path(start, endTemp, self.grid)
                if minPath > len(pathTemp):
                    cajacerca = boxPos
                    minPath = len(pathTemp)
        else:
            #si estan acmododadas, el robot se mueve a la casilla 1,1
            cajacerca = (1,1)
        #aplicar una vez mas AStar con el camino mas cercano encontrado
        self.grid.cleanup()
        grid = GridPath(matrix= self.matrix)
        self.grid = grid
        end = self.grid.node(cajacerca[0], cajacerca[1])
        path, runs = finder.find_path(start, end, self.grid)
        if(len(path) > 1):
            #si el siguiente movimiento es la posicion de la caja, activas las flags de dicha caja y procedes de dejar la caja
            # a la pila mas cercana con el booleano gotBox
            next_move = path[1]
            if cajacerca == self.pos:
                next_move = path[0]
            if next_move in self.model.initialBoxesPos.keys():
                self.carryingBox = self.model.initialBoxesPos[next_move]
                self.carryingBox.inRobot = True
                self.model.initialBoxesPos.pop(next_move)
                self.gotBox = True
            self.model.grid.move_agent(self, next_move)
    
    #metodo para dejar la caja del robot en la pila mas cercana que tenga menos de 5 cajas empleando aStar
    def leaveBox(self):
        minPath = 100
        self.grid.cleanup()
        grid = GridPath(matrix= self.matrix)
        self.grid = grid
        start = self.grid.node(self.pos[0], self.pos[1])
        stackNear = self.pos
        finder = AStarFinder(diagonal_movement = DiagonalMovement.never)
        #busqueda de la pila más cercana con menos de 5 cajas almacenadas por AStar
        for stack in self.model.stacksPos.keys():
            if (self.model.stacksPos[stack].boxCounter < 5):
                self.grid.cleanup()
                grid = GridPath(matrix= self.matrix)
                self.grid = grid
                endTemp = self.grid.node(stack[0], stack[1])
                pathTemp, runsTemp = finder.find_path(start, endTemp, self.grid)
                if minPath > len(pathTemp):
                    minPath = len(pathTemp)
                    stackNear = stack
        #implementacion de AStar con el camino más cercano
        self.grid.cleanup()
        grid = GridPath(matrix= self.matrix)
        self.grid = grid
        end = self.grid.node(stackNear[0], stackNear[1])
        path, runs = finder.find_path(start, end, self.grid)
        if(len(path) > 1):
            next_move = path[1]
            #si el siguiente movimiento del path es un stack y ese stack tiene menos de 5 cajas
            if next_move in self.model.stacksPos.keys() and self.model.stacksPos[next_move].boxCounter < 5:
                #asignamos las flags de la caja con los valores del orden en el que entro al stack
                self.model.stacksPos[next_move].boxCounter += 1
                self.carryingBox.inStack = self.model.stacksPos[next_move].boxCounter
                self.carryingBox.inRobot = False
                #el robot vuelve a buscar la caja desordenada más cercana
                self.gotBox = False
            self.carryingBox.pos = next_move
            self.model.grid.move_agent(self, next_move)
#Modelo del almacen, en donde se inicializa el grid , la cantidad de agentes a interactuar                
class Maze(Model):
    def __init__(self):
        super().__init__()
        self.schedule = RandomActivation(self)
        self.grid = MultiGrid(10, 10, torus=False)
        self.availableCells = 0
        self.amountOfAgents = 5
        self.amountOfBoxes = 20
        self.initialBoxesPos = {}
        self.stacksPos = {}
        self.allBoxesOrdered = False
        self.steps = 0
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
        #establecimiento de muros
        for _,x,y in self.grid.coord_iter():
            if self.matrix[y][x] == 0:
                block = WallBlock(self, (x, y))
                self.grid.place_agent(block, block.pos)
                self.schedule.add(block)
            else:
                self.availableCells += 1
        #validar que las cajas entren en el grid
        self.availableCells -= self.amountOfAgents
        if (self.amountOfBoxes > self.availableCells):
            self.amountOfBoxes = 30
        #obtener la cantidad de pilas a insertar en el grid
        self.amountOfStacks = self.amountOfBoxes//5
        if self.amountOfBoxes % 5 > 0:
            self.amountOfStacks += 1
        k = 8
        for j in range(1,self.amountOfStacks + 1):
            if (j > 8):
                j = 1
                k = k - 1
            stack = Stack(self,(k,j))
            self.grid.place_agent(stack, (j , k))
            self.schedule.add(stack)
            self.stacksPos[(j,k)] = stack
        #insertar robots en el grid
        for i in range(self.amountOfAgents):
            random_pos = self.grid.find_empty()
            x = random_pos[1]
            y = random_pos[0]
            if self.matrix[x][y] == 1:
                bender = Robot(self, (y,x))
                self.grid.place_agent(bender, (y,x))
                self.schedule.add(bender)
            else:
                i = i - 1
        #insertar cajas en el grid
        for i in range(self.amountOfBoxes):
            random_pos = self.grid.find_empty()
            x = random_pos[1]
            y = random_pos[0]
            if self.matrix[x][y] == 1:
                caja = Caja(self, (x,y))
                self.grid.place_agent(caja, (y,x))
                self.schedule.add(caja)
                self.initialBoxesPos[(y,x)] = caja
            else:
                i = i - 1
    def step(self):
        boxesInStack = 0
        self.schedule.step()
        self.steps += 1
        #imprime los contadores de cada stack
        for stack in self.stacksPos:
            if not self.allBoxesOrdered:
                print ("Cajas en Stack ",stack," -> ",self.stacksPos[stack].boxCounter)
                boxesInStack += self.stacksPos[stack].boxCounter
        #si todas las cajas ya se ordenaron se despliega la información de la simulación
        if boxesInStack == self.amountOfBoxes and not self.allBoxesOrdered:
            self.allBoxesOrdered = True
            print ("-------- TODAS LAS CAJAS ORDENADAS EN PILAS ----------")
            print ("Tiempo total (en pasos): ", self.steps )
            print ("Pasos realizados por los robots: ", self.steps * self.amountOfAgents)
            print("Presiona Ctrl+C para terminar la simulación")
            sys.exit(0)