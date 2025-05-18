.. python-lekin documentation master file, created by
   sphinx-quickstart on Fri Sep 30 17:57:17 2022.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

python-lekin documentation
========================================
.. raw:: html

   <a class="github-button" href="https://github.com/HongyingYue/python-lekin" data-icon="octicon-star" data-size="large" data-show-count="true" aria-label="Star HongyingYue/python-lekin on GitHub">GitHub</a>


**python-lekin** 是一个工厂智能排产调度工具，名字来源于`Lekin <https://web-static.stern.nyu.edu/om/software/lekin/>`_.


车间排产快速入门
-----------------------

排产是一个分配任务，将有限的资源分配给需求。因此需求需要有优先级，约束主要有产能约束与物料约束。产能约束，将订单中的成品按工艺路线分解为工序，而每一道工序有对应的生产机器；物料约束，将订单的成品按BOM(bill of materials)展开为原材料需求，每一道工序开始前需要对应原材料齐套。

更直白来讲，就是把工序任务分配在资源和时间上。目标是总完成时间最小，换型最少等。工序任务，上级有需求(需求带有优先级)，平级有工序先后关系，和资源的关系有可用资源和资源优先级, 时长；资源有日历。

下标，机器k kk加工为任务i ii后加工任务j jj

其中，:math:`A_\text{c} = (\pi/4) d^2`


subject to:

.. math:: \alpha{}_t(i) = P(O_1, O_2, … O_t, q_t = S_i \lambda{})

Flexible Job-Shop Scheduling problem（FJSP）包含两个任务
- Machine assignment: 选择机器
- Operation sequencing：工序顺序


Finite Capacity Planning


.. toctree::
   :maxdepth: 2
   :caption: Contents:

   rules
   heuristics
   application
   GitHub <https://github.com/HongyingYue/python-lekin>


Indices and tables
=========================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
