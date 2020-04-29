'''
This is the file controlling all hypers
calling different components
and executing experiments
'''

# python3's own
import time
import numpy as np
import sys
import random
from pprint import pprint

# we wrote them
from handleInput import *
from handleOutput import *
from qLearning import *

def hypers(truckCapacity, lengthOfRoad, startingPenalty, maxClockTicks, seed):
	'''
	all hypers should be defined here
	returning the dict of them
	'''

	hyperDict = {
		"randomSeed": seed,

		# settings for search
		"initCreateProb": 0.13,
		"increaseProb": 0.02,
		"decreaseProb": -0.02,
		"probUpperBound": 0.25,
		"probLowerBound": 0.05,
		"deliveryMultiplier": 30,
		"defaultMaxTime": 1000,
		
		# not sure if we will use them
		# ours:0, ramdom:1, epsilon-greedy:2
		"lambda":	0,
		"algorithm": 0,
		"epsilon": 0.1,

		# predefined by cmd line input
		"truckCapacity": truckCapacity,
		"startTruckPenalty": startingPenalty,
		"lengthOfRoad": lengthOfRoad,
		"maxTime":	maxClockTicks,
	}

	if hyperDict["maxTime"] == -1:
		hyperDict["maxTime"] = hyperDict["defaultMaxTime"]

	# pprint(hyperDict)

	return hyperDict


def main(seed=1):
	# read inputs
	try:
		truckCapacity, lengthOfRoad, startingPenalty, maxClockTicks = readInput()
	except Exception as e:
		return False

	# make up hypers
	hyperDict = hypers(truckCapacity, lengthOfRoad, startingPenalty, maxClockTicks, seed)

	# set random sequence
	random.seed(hyperDict["randomSeed"])
	
	# run the program
	results = search(**hyperDict)

	# generate output
	# status = writeFile(results)
	

	return True


if __name__ == '__main__':
	# set up default display mode
	np.set_printoptions(threshold=sys.maxsize)
	# set random sequence
	seed = 1
	# seed = time.time()
	random.seed(seed)
	np.random.seed(seed)
	# now ready to go
	main(seed=seed)
# sample cmd line to evoke:
# python3 expSearch.py 20 10 -10 3