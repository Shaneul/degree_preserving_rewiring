# Installation

## From source

```console
git clone https://github.com/Shaneul/degree_preserving_rewiring
cd degree_preserving_rewiring
pip install .

```

# Example

Simple example rewiring a random graph.
```python
import networkx as nx
from degree_preserving_rewiring import rewire

G = nx.erdos_renyi_graph(5000, p = 5/4999, seed = 42)
G, results = rewire(G, 0.4, 'random graph', sample_size=20, timed=True, 
                    time_limit=120, method='new')

```

# TODO

- [ ] Update setup.py, rebuild package and bump version
- [ ] Any additional result handling code should be handled outside the package depending on use case
- [x] Add more detailed results handling code
- [x] Make the changes to the negative rewiring code that have been made to the
      positive rewiring code
- [x] For simulating large numbers of graphs, we will not want detailed dataframes
      so add  something to summarise the results of each rewiring of a graph
      i.e., total number of edges rewired, etc.
- [x] Edit the negative rewiring full code
- [x] Each of the sample rewiring codes needs to be edited
