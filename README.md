[license-image]: https://img.shields.io/badge/License-Apache%202.0-blue.svg
[license-url]: https://opensource.org/licenses/Apache-2.0
[pypi-image]: https://badge.fury.io/py/lekin.svg
[pypi-url]: https://pypi.python.org/pypi/lekin
[pepy-image]: https://pepy.tech/badge/lekin
[pepy-url]: https://pepy.tech/project/lekin
[build-image]: https://github.com/HongyingYue/python-lekin/actions/workflows/test.yml/badge.svg?branch=main
[build-url]: https://github.com/HongyingYue/python-lekin/actions/workflows/test.yml?query=branch%3Amain
[lint-image]: https://github.com/HongyingYue/python-lekin/actions/workflows/lint.yml/badge.svg?branch=main
[lint-url]: https://github.com/HongyingYue/python-lekin/actions/workflows/lint.yml?query=branch%3Amain
[docs-image]: https://readthedocs.org/projects/python-lekin/badge/?version=latest
[docs-url]: https://python-lekin.readthedocs.io/en/latest/
[coverage-image]: https://codecov.io/gh/HongyingYue/python-lekin/branch/main/graph/badge.svg
[coverage-url]: https://codecov.io/github/HongyingYue/python-lekin?branch=main

<h1 align="center">
<img src="./docs/source/_static/logo.svg" width="400" align=center/>
</h1><br>

[![LICENSE][license-image]][license-url]
[![PyPI Version][pypi-image]][pypi-url]
[![Download][pepy-image]][pepy-url]
[![Build Status][build-image]][build-url]
[![Lint Status][lint-image]][lint-url]
[![Docs Status][docs-image]][docs-url]
[![Code Coverage][coverage-image]][coverage-url]

**[Documentation](https://python-lekin.readthedocs.io)** | **[Tutorials](https://python-lekin.readthedocs.io/en/latest/tutorials.html)** | **[Release Notes](https://python-lekin.readthedocs.io/en/latest/CHANGELOG.html)** | **[中文](https://github.com/hongyingyuen/python-lekin/blob/main/README_zh_CN.md)**

**python-lekin** is a Flexible Job Shop Scheduler Library, named after [Lekin](https://web-static.stern.nyu.edu/om/software/lekin/).
As a core function in **APS (advanced planning and scheduler)**, it helps manufacturers optimize the allocation of materials and production capacity optimally to balance demand and capacity.

- Changeover Optimization
- Ready for demo, research and maybe production

# **DEVELOPING - NOT FINISHED AND DON'T USE IT NOW!**


## Features

- Multiple solving strategies:
  - Continuous Time Planning (CTP)
  - Construction Heuristics
  - Meta-heuristics (Genetic Algorithm, Simulated Annealing)
  - Reinforcement Learning
  - Operation Research methods
- Extensible architecture for custom solvers
- Comprehensive constraint handling
- Performance metrics and visualization
- Parallel solving capabilities
- Solution validation and verification


## Tutorial

[![Open In Colab](https://colab.research.google.com/drive/1zHqYZFZNvLE7aoDcBUh7TCK7oHfXQkLi?usp=sharing)]

**Installation**

``` shell
pip install lekin
```

**Usage**

``` python
from lekin import Heuristics, Rule
from lekin import Scheduler

solver = Rule('SPT')
scheduler = Scheduler(solver)
scheduler.solve(job_list, machine_list)

scheduler.draw()
```

## Examples

In real world, Lekin integrates with MES to deploy production plans on the shop floor. Integration with ERP system is also required to exchange information on demand, inventory, and production

- Exhaustive search
  - branch and bound

- Construction heuristics
    - [SPT]()
    - [critical path]()

- Meta heuristics
    - [local search]()
      - [hill climbing]()
      - [tabu search]()
    - [evolutionary algorithms]()
      - [genetic algorithms]()

- Operation search
    - [or-tools]()

- Reinforcement learning

Metaheuristics combined with Construction
Heuristics to initialize is the recommended choice.


### Adding New Constraints

```python
from lekin.solver.constraints import BaseConstraint

class MyCustomConstraint(BaseConstraint):
    def check(self, solution):
        # Implement your constraint checking logic
        pass
```



## Citation
```
@misc{python-lekin2022,
  author = {Hongying Yue},
  title = {python lekin},
  year = {2022},
  publisher = {GitHub},
  journal = {GitHub repository},
  howpublished = {\url{https://github.com/hongyingyue/python-lekin}},
}
```
