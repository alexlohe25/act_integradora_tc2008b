from mesa import Agent, Model
from mesa.space import Grid, MultiGrid
from mesa.time import RandomActivation
from mesa.visualization.modules import CanvasGrid
from mesa.visualization.ModularVisualization import ModularServer

from pathfinding.core.diagonal_movement import DiagonalMovement
from pathfinding.core.grid import Grid as GridPath
from pathfinding.finder.a_star import AStarFinder

import sys

class WallBlock(Agent):
    def __init__(self, model, pos):
        super().__init__(model.next_id(), model)
        self.pos = pos
    def step(self):
        pass
class Stack(Agent):
    def __init__(self, model, pos):
        super().__init__(model.next_id(), model)
        self.pos = pos
        self.model = model
        self.boxCounter = 0
    def step(self):
        pass
class Caja(Agent):
    def __init__(self, model, pos):
        super().__init__(model.next_id(), model)
        self.pos = pos
        self.inStack = 1
        self.inRobot = False
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
        if not self.gotBox:
            self.collectBox()
        else:
            self.leaveBox()


    def collectBox(self):
        minPath = 100
        self.grid.cleanup()
        grid = GridPath(matrix= self.matrix)
        self.grid = grid
        start = self.grid.node(self.pos[0], self.pos[1])
        allBoxesinStack = bool(self.model.initialBoxesPos)
        finder = AStarFinder(diagonal_movement = DiagonalMovement.never)
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
            cajacerca = (1,1)
        self.grid.cleanup()
        grid = GridPath(matrix= self.matrix)
        self.grid = grid
        end = self.grid.node(cajacerca[0], cajacerca[1])
        path, runs = finder.find_path(start, end, self.grid)
        if(len(path) > 1):
            next_move = path[1]
            if cajacerca == self.pos:
                next_move = path[0]
            if next_move in self.model.initialBoxesPos.keys():
                self.carryingBox = self.model.initialBoxesPos[next_move]
                self.carryingBox.inRobot = True
                #self.model.boxesFound.append(self.model.initialBoxesPos[next_move])
                self.model.initialBoxesPos.pop(next_move)
                self.gotBox = True
            self.model.grid.move_agent(self, next_move)
    
    
    def leaveBox(self):
        minPath = 100
        self.grid.cleanup()
        grid = GridPath(matrix= self.matrix)
        self.grid = grid
        start = self.grid.node(self.pos[0], self.pos[1])
        stackNear = self.pos
        finder = AStarFinder(diagonal_movement = DiagonalMovement.never)
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
        self.grid.cleanup()
        grid = GridPath(matrix= self.matrix)
        self.grid = grid
        end = self.grid.node(stackNear[0], stackNear[1])
        path, runs = finder.find_path(start, end, self.grid)
        if(len(path) > 1):
            next_move = path[1]
            if next_move in self.model.stacksPos.keys() and self.model.stacksPos[next_move].boxCounter < 5:
                #caja = Caja(self.model, next_move)
                
                #self.model.grid.place_agent(caja, next_move)
                #self.model.schedule.add(caja)
                self.model.stacksPos[next_move].boxCounter += 1
                self.carryingBox.inStack = self.model.stacksPos[next_move].boxCounter
                self.carryingBox.inRobot = False
                self.gotBox = False
                #if self.model.stacksPos[next_move].boxCounter == 5:
                #    self.model.matrix[self.pos[0]][self.pos[1]] = 0
            self.carryingBox.pos = next_move
            self.model.grid.move_agent(self, next_move)
                
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
        self.boxesFound = []
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
        for _,x,y in self.grid.coord_iter():
            if self.matrix[y][x] == 0:
                block = WallBlock(self, (x, y))
                self.grid.place_agent(block, block.pos)
                self.schedule.add(block)
            else:
                self.availableCells += 1
        self.availableCells -= self.amountOfAgents
        if (self.amountOfBoxes > self.availableCells):
            self.amountOfBoxes = 30
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
        for boxToMove in self.boxesFound:
            self.grid.remove_agent(boxToMove)
            self.schedule.remove(boxToMove)
            self.boxesFound.remove(boxToMove)
        for stack in self.stacksPos:
            if not self.allBoxesOrdered:
                print ("Cajas en Stack ",stack," -> ",self.stacksPos[stack].boxCounter)
                boxesInStack += self.stacksPos[stack].boxCounter
        if boxesInStack == self.amountOfBoxes and not self.allBoxesOrdered:
            self.allBoxesOrdered = True
            print ("-------- TODAS LAS CAJAS ORDENADAS EN PILAS ----------")
            print ("Tiempo total (en pasos): ", self.steps )
            print ("Pasos realizados por los robots: ", self.steps * self.amountOfAgents)
            print("Presiona Ctrl+C para terminar la simulación")
            sys.exit(0)