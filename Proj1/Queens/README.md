# Queens
## How to run the code
### Prerequisites
#### Operating systems
We tested on the most up to dated
* Windows 10
* Mac OS
* Linux Ubuntu 18.04
Users are safe to run our code on these platforms. For other platforms, generally speaking, it should also be fine but we cannot fully guarantee as no test was executed.
#### Language
To run the code you will need to install `python3`. Any version no earlier than `V3.5` will be fine.
#### Dependency
You would also need the following packages/libraries. Usually they are already automatically integrated together with python3. 
```
numpy
sys
heapq
time
random
copy
math
collections
```
### Command line
Open terminal and change directory to the Queens folder, then run the following command
```shell
python3 HeavyQueens.py [boardFileName] [1|2|3] [h1|h2|h3]
```
For detailed explanation of each argv, you can simply run the following command:
```shell
python3 HeavyQueens.py
```
## Execution Results
Results will be printed out automatically. The following information will be shown:
* Your input choice
* The start state
* Time to solve the puzzle
* The effective branching factor
* The cost to solve the puzzle
* The sequence of moves needed to solve the puzzle, if any

