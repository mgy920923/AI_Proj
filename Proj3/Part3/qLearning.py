'''
the actual q learning file
for the exact search algorithm
'''

# import numpy as np

from expSearch import *
import time
import numpy as np
import random
import itertools


class environment(object):
    """docstring for environment"""

    def __init__(self, **kwargs):
        super(environment, self).__init__()

        warehouseDict = {
            "initProb": kwargs["initCreateProb"],
            "probUpperBound": kwargs["probUpperBound"],
            "probLowerBound": kwargs["probLowerBound"],
            "increaseProb": kwargs["increaseProb"],
            "decreaseProb": kwargs["decreaseProb"],
        }

        truckDict = {
            "capacity": kwargs["truckCapacity"],
            "multiplier": kwargs["deliveryMultiplier"],
            "startPenalty": kwargs["startTruckPenalty"]
        }

        self.warehouse = warehouse(**warehouseDict)
        self.truck = truck(**truckDict, env=self)

        self.reward = 0
        self.clock = 0
        self.lengthOfRoad = kwargs["lengthOfRoad"]
        self.maxTime = kwargs["maxTime"]

        self.algorithm = kwargs["algorithm"]
        self.Q_table = kwargs["Q_table"] if "Q_table" in kwargs else None
        self.eps = kwargs["epsilon"]
        self.truck_package_quantiles = kwargs["truck_package_quantiles"]
        self.warehouse_package_quantiles = kwargs["warehouse_package_quantiles"]

        self.packageNotOnTruck = []

    def _iteration(self, **kwargs):
        # first check ending standard
        if self.clock >= self.maxTime:
            return False
        self.clock += 1

        # then update warehouse and truck
        result = self.warehouse.updateWarehouse(self.clock, self.lengthOfRoad)
        self.truck.updatePos()

        # load into lists
        if result is not None:
            self.packageNotOnTruck.append(result)

        # is the truck currently at warehouse?
        if self.truck.currentPos == 0:
            # load on truck, update remaining
            self.packageNotOnTruck = self.truck.loadPackage(self.packageNotOnTruck)
            # start the truck or not
            flag = self.truck.decideAction()
            # you decide the inputs
            # TODO: Figure out how to Q_update for actions below
            if flag:
                self.truck.startDeliver()  # calculate reward, leaving warehouse
            else:
                self.truck.wait()  # stay for the next clock tick
        # on its way, deliver things
        else:
            self.truck.deliver(self.lengthOfRoad)

        # for every package not yet delivered, calculate penalty
        if len(self.packageNotOnTruck) > 0:
            timeDiff1 = sum([self.clock - package.createTime for package in self.packageNotOnTruck])
        else:
            timeDiff1 = 0

        if len(self.truck.packageList) > 0:
            timeDiff2 = sum([self.clock - package.createTime for package in self.truck.packageList])
        else:
            timeDiff2 = 0

        self.truck.reward -= (timeDiff1 + timeDiff2)
        return True

    def simulation(self):
        # 1. test: strategy 0: pass!
        # 2. test: strategy 1: pass!

        while self._iteration():
            # do anything

            # prints for debug, comment out in real case
            self._stepCheck()

            # 3. test: only do one step, uncomment next line
            # break

        return  # up to you about what to return

    def _stepCheck(self):
        print("Clock time:\t", self.clock)
        print("-------------------------------------------")
        print("Warehouse Check:")
        print("Prev Status Create Package:\t", self.warehouse.prevStatus)
        print("Prev Prob Create Package:\t", self.warehouse.prevProb)
        print("#Packages left in house:\t", len(self.packageNotOnTruck))
        print("Destinations:\t\t\t", [item.deliverHouse for item in self.packageNotOnTruck])
        print("-------------------------------------------")
        print("Truck Check:")
        print("Truck Position:\t\t\t", self.truck.currentPos)
        print("#Packages left on truck:\t", len(self.truck.packageList))
        print("Destinations:\t\t\t", [item.deliverHouse for item in self.truck.packageList])
        print("Current Truck Reward:\t\t", self.truck.reward)
        print("")
        return True


class truck(object):
    """docstring for truck"""

    def __init__(self, capacity, multiplier, startPenalty, env: environment):
        super(truck, self).__init__()
        self.capacity = capacity
        self.multiplier = multiplier
        self.currentPos = 0
        self.longestDestination = 0
        self.packageList = []
        self.reward = 0
        self.startPenalty = startPenalty
        self._environment = env
        self.state = ()

        # 0: stay; 1: move forward; -1: move backward
        self.nextStep = 0

    def loadPackage(self, packageList):
        # upload the packages to truck until capacity
        # return the remaining packages
        # FIFO
        emptySpace = self.capacity - len(self.packageList)
        self.packageList += packageList[:emptySpace]
        packageList = packageList[emptySpace:]
        return packageList

    def decideAction(self):
        # whether to wait:False or start:True
        strategy = self._environment.algorithm
        if strategy == 0:
            # dummy strategy 0: always start so long as its not empty
            # this is for debugging
            # comment out for real case
            flag = True if len(self.packageList) > 0 else False

        elif strategy == 1:
            # dummy strategy 1: only start when it is full
            # this is for debugging
            # comment out for real case
            flag = True if len(self.packageList) == self.capacity else False

        # you design other strategies
        else:
            chooseAction = self.recommendedPolicyAction()
            flag = bool(self.chosenAction(chooseAction, self._environment.eps))

        return flag

    def get_state(self):
        if len(self.packageList) == 0:
            truck_package_quantile = 0
        else:
            truck_package_quantile = int((len(self.packageList) / self.capacity) //
                                         (1 / self._environment.truck_package_quantiles) + 1)

        numPackagesInWarehouse = len(self._environment.packageNotOnTruck)
        if numPackagesInWarehouse == 0:
            warehouse_package_quantile = 0
        elif numPackagesInWarehouse < self.capacity:
            warehouse_package_quantile = int((numPackagesInWarehouse / self.capacity) //
                                             (1 / self._environment.warehouse_package_quantiles) + 1)
        else:
            warehouse_package_quantile = self._environment.warehouse_package_quantiles + 1

        return self._environment.warehouse.prevProb, truck_package_quantile, warehouse_package_quantile

    def recommendedPolicyAction(self):
        searchType = self._environment.algorithm
        # return direction based on algorithm
        if searchType in [0, 1]:
            return random.randint(0, 1)

        elif searchType == 2:
            self.state = self.get_state()

            actions = self._environment.Q_table[self.state]
            max_value = np.max(actions)
            choices = [index for index, value in enumerate(actions) if value == max_value]
            return np.random.choice(choices, 1)[0]
        return 0

    @staticmethod
    def chosenAction(action, eps):
        return random.choice([0, 1]) if random.random < eps else action

    def startDeliver(self):
        self.nextStep = 1
        self.reward += self.startPenalty
        return True

    def deliver(self, lengthOfRoad):
        # split packages according to destination
        arrivedPackage = [package for package in self.packageList if package.deliverHouse == self.currentPos]
        self.packageList = [package for package in self.packageList if package.deliverHouse != self.currentPos]
        # delivery reward
        self.reward += self.multiplier * lengthOfRoad * len(arrivedPackage)
        # update next step strategy
        if len(self.packageList) > 0:
            self.nextStep = 1
        else:
            self.nextStep = -1

        return True

    def wait(self):
        # next step still same place
        self.nextStep = 0
        return True

    def updatePos(self):
        self.currentPos += self.nextStep

    def Q_update(self):
        pass


class warehouse(object):
    """docstring for warehouse"""

    def __init__(self, initProb, probUpperBound, probLowerBound, increaseProb, decreaseProb):
        super(warehouse, self).__init__()
        self.prevProb = initProb
        # True for generated, False for not generated
        self.prevStatus = True

        self.probUpperBound = probUpperBound
        self.probLowerBound = probLowerBound
        self.increaseProb = increaseProb
        self.decreaseProb = decreaseProb

    def _getProb(self):
        if self.prevStatus:
            prob = min(self.prevProb + self.increaseProb, self.probUpperBound)
        else:
            prob = max(self.prevProb + self.decreaseProb, self.probLowerBound)
        return prob

    def _updateProb(self, prob):
        self.prevProb = prob

    def _updateStatus(self, status):
        self.prevStatus = status

    def _getStatus(self, prob):
        # tell whether it should create new package
        state = random.random()
        if state < prob:
            status = True
        else:
            status = False
        return status

    def _createPackage(self, timestamp, lengthOfRoad):
        deliverHouse = random.randint(1, lengthOfRoad)
        newPackage = package(timestamp, deliverHouse)
        return newPackage

    def updateWarehouse(self, timestamp, lengthOfRoad):
        # get new prob and status
        prob = self._getProb()
        status = self._getStatus(prob)
        # update new prob and status
        self._updateProb(prob)
        self._updateStatus(status)
        # generate new package or not, return object
        if status:
            return self._createPackage(timestamp, lengthOfRoad)
        return None


class package(object):
    """docstring for package"""

    def __init__(self, createTime, deliverHouse):
        super(package, self).__init__()
        self.createTime = createTime
        self.deliverHouse = deliverHouse


def init_Q_table(env, truck_packages_quantiles=4, warehouse_packages_quantiles=4):
    Q_table = {}
    vals = [list(np.round(np.linspace(env.warehouse.probLowerBound, env.warehouse.probUpperBound,
                                      (env.warehouse.probUpperBound - env.warehouse.probLowerBound) /
                                      env.warehouse.increaseProb + 1), 2)),
            list(range(0, truck_packages_quantiles + 2)), list(range(0, warehouse_packages_quantiles + 2))]

    for val in itertools.product(*vals):
        Q_table[val] = {"numVisits": 0, "Q": [0, 0]}

    return Q_table


def search(**kwargs):
    '''
    placeholder func
    '''
    game = environment(**kwargs)
    Q_table = init_Q_table(game)
    game.Q_table = Q_table
    decay_rate = kwargs["decay_rate"]

    done = False
    epoch = 0

    while not done:
        kwargs["Q_table"] = game.Q_table
        game.simulation()
        game.__init__(**kwargs)
        kwargs["epsilon"] *= decay_rate
        epoch += 1

    return {}  # up to designers
