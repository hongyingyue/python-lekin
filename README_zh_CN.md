[license-image]: https://img.shields.io/badge/License-Apache%202.0-blue.svg
[license-url]: https://opensource.org/licenses/Apache-2.0
[pypi-image]: https://badge.fury.io/py/lekin.svg
[pypi-url]: https://pypi.python.org/pypi/python-lekin
[pepy-image]: https://pepy.tech/badge/lekin/month
[pepy-url]: https://pepy.tech/project/lekin
[build-image]: https://github.com/HongyingYue/python-lekin/actions/workflows/test.yml/badge.svg?branch=main
[build-url]: https://github.com/HongyingYue/python-lekin/actions/workflows/test.yml?query=branch%3Amain
[lint-image]: https://github.com/HongyingYue/python-lekin/actions/workflows/lint.yml/badge.svg?branch=main
[lint-url]: https://github.com/HongyingYue/python-lekin/actions/workflows/lint.yml?query=branch%3Amain
[docs-image]: https://readthedocs.org/projects/python-lekin/badge/?version=latest
[docs-url]: https://python-lekin.readthedocs.io/en/latest/

<h1 align="center">
<img src="./docs/source/_static/logo.svg" width="400" align=center/>
</h1><br>

[![LICENSE][license-image]][license-url]
[![PyPI Version][pypi-image]][pypi-url]
[![Download][pepy-image]][pepy-url]
[![Build Status][build-image]][build-url]
[![Lint Status][lint-image]][lint-url]
[![Docs Status][docs-image]][docs-url]

**[文档](https://python-lekin.readthedocs.io)** | **[教程](https://python-lekin.readthedocs.io/en/latest/tutorials.html)** | **[发布日志](https://python-lekin.readthedocs.io/en/latest/CHANGELOG.html)** | **[English](https://github.com/HongyingYue/python-lekin/blob/main/README.md)**

**python-lekin**是一个APS智能排产调度工具。考虑实际约束的前提下，实现动态调整计划排程，高效响应客户订单承诺。

- 支持工艺路线约束
- 支持产能约束
- 支持物料齐套约束
- 支持顺排、倒排等排产方法
- 支持遗传算法排产
- 支持强化学习排产

# **开发中- 目前请不要使用包，可用代码跑和学习!**

## 快速入门

[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/drive/1zHqYZFZNvLE7aoDcBUh7TCK7oHfXQkLi?usp=sharing)


### 安装

``` shell
$ pip install lekin
```

### 使用

``` python
from lekin import Heuristics, Genetics
from lekin import Scheduler

solver = Heuristics()
scheduler = Scheduler(solver)
scheduler.solve(jobs, machines)

scheduler.draw()
```

## 示例
在实际APS系统开发中，

- 按工艺路线拆分工序
- 按BOM拆分物料

### 数据准备

- Job
- Task
- Machine
- Route


## 引用

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
