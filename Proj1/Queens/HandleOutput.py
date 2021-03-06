from Board import *


def handleTime(elapsedTime):
    # better format the elapsedTime into hour,min,sec,msec
    timeString = "{} hour {} min {} sec {} msec".format(elapsedTime // 3600, (elapsedTime % 3600) // 60,
                                                        int(elapsedTime % 60), int(1000 * (elapsedTime % 1)))
    return timeString


def generateOutput(searchResults):
    print("Search Done! Generating output report ...")

    if "solved" in searchResults:
        if searchResults["solved"]:
            print("\nSolution found for greedy hill climbing! :D\n")
        else:
            print("\nSolution NOT found for greedy hill climbing! :(\n")
    print("The initial board state:")
    printBoard(searchResults["initBoard"])
    print("")

    print("#Nodes expanded:", searchResults["expandNodeCount"])
    print("Time elapsed:", handleTime(searchResults["elapsedTime"]))
    if "bestSolutionTime" in searchResults:
        print("Time to best solution:", handleTime(searchResults["bestSolutionTime"]))
    print("Effective branching factor:", searchResults["branchingFactor"])
    print("Cost of moves:", searchResults["cost"])
    print("-------------------------------------------")
    print("Seq of moves:")
    printMoves(searchResults["sequence"])
    print("")

    print("That is all, ty for testing on our program.")
    return True
