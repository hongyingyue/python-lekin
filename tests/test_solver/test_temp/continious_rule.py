# 连续排产的规则调整

from dataclasses import dataclass


@dataclass
class OP:
    id: int
    val: int


op1 = OP(id=1, val=0)
op2 = OP(id=2, val=1)
op3 = OP(id=3, val=0)
op4 = OP(id=4, val=1)
op5 = OP(id=5, val=1)
op6 = OP(id=6, val=0)
op7 = OP(id=7, val=0)
op8 = OP(id=8, val=1)
op9 = OP(id=9, val=1)
op10 = OP(id=10, val=0)
op11 = OP(id=11, val=0)
op12 = OP(id=12, val=0)
op13 = OP(id=13, val=1)

op_list = [eval(f"op{i}") for i in range(1, 14)]

prefix = 4
suffix = 13

i = max(prefix - 1, 0)
while i < suffix:

    print(i)
    insert_index = i + 1
    j = i + 1
    while j < suffix and op_list[j].val == op_list[i].val:
        j += 1
        insert_index += 1

    while j < suffix:
        if j != insert_index and op_list[j].val == op_list[i].val:
            op_list.insert(insert_index, op_list.pop(j))
            insert_index += 1
        j += 1

    i = insert_index
    print(i)
    print([op.id for op in op_list])
    print([op.val for op in op_list])
    print("-" * 30)


print([op.id for op in op_list])
print([op.val for op in op_list])
