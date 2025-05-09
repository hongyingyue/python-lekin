规则排产
============

分为rule-based、event-based、resource-based两种思路。

SPT最短加工时间
--------------------

按任务所需工序时间长短，从短到长顺序排列.
实现中，为保证工艺路径的先后约束关系，构造规则法通过循环的先后关系来保证满足约束。


EDD最早预定交货期规则
---------------------------

按生产任务规定完成时刻（预定交货期）的先后，从先到后顺次排列

SPT—EDD规则
-----------------

1）根据EDD规则安排D(max)为最小的方案。
2）计算所有任务的总流程时间。
3）查找方案中，预定交贷期（di）大于总流程时间的生产任务（不惟一），按SPT规则，将其中加工时间最大者排于最后。
4）舍弃第3步能排定的最后任务者及其后序任务，回到第2步重复。


关键路径法
-------------

关键路径是决定项目完成的最短时间，关键路径可能不止一条。

其基本概念：
最早开始时间 (Early start)
最晚开始时间 (Late start)
最早完成时间 (Early finish)
最晚完成时间 (Late finish)
松弛时间 (slack)

正推方法确定每个任务的最早开始时间和最早完成时间，逆推方法确定每个任务的最晚完成时间和最晚开始时间。


顺排
-------------

顺排和倒排，和其他规则启发式算法一样，一个工序集一个工序集的排。每排一个工序，工序job完成后，更新机器、job状态、后续job状态。
顺排对下一道工序的约束是：最早开始时间

.. code-block:: python

    backward(operations, next_op_start_until, with_material_kitting_constraint, align_with_same_production_line, latest_start_time, latest_end_time)


.. code-block:: python

    assign_op(operation, is_critical, direction: str)

在顺排中，排的比较紧密的资源往往就是瓶颈资源。

倒排
---------------

每一个MO最早开始时间初始化：max(ESD, today)。确保开始时间不早于今天，或不早于资源日历最早开始时间
倒排对下一道工序的约束是: 最晚结束时间

倒排
- 从业务上可以减少库存, just-in-time
- 带来的结果是不连续
- 影响连续排产的判断
- 考虑物料齐套时，导致倒排可能需要一次次推倒重来


.. code-block:: python

    forward(operations, next_op_start_until, with_material_kitting_constraint,  align_with_same_production_line, earliest_start_time, earliest_end_time)



终局
----------------------

规则启发在排产中的应用，进行足够的抽象后，灵活使用多种方法的结合。

一批次可开始的。剩余未开始的
- 那么，可开始的是否一定要比未开始的先开始呢？其实不是
- 那么通过工序图的依赖关系，其实给定了每个工序的最早开始时间约束。甚至不是具体的时间，而是一个变量之间的
