from HandleInput import *
from HandleOutput import *
from algo import *
from Rules import *


def search(targetMap,searchType):
    if searchType == "ga":
        result = genetic(targetMap)
    elif searchType == "hc":
        result = greedyHillClimb(targetMap)
    else:
        result = greedyHillClimb(targetMap, mode="super_greedy")
    return result


def main():
    industrial, commercial, residential, siteMap, searchType = readInput()
    targetMap = Map(mapState=siteMap, maxIndustrial=industrial, maxCommercial=commercial, maxResidential=residential)
    result = search(targetMap, searchType)
    # output not done yet

    return True


if __name__ == '__main__':
    main()
