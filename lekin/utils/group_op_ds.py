"""
新加入的时候可以快速找到该节点，因此之前用了dict[id, MaterialOP]

移动的时候, 先标记一些candidate

找到一个candidate, 往前找之前的插入位置

重新整理

"""


class DictNode:
    def __init__(self, key, value):
        self.key = key
        self.value = value
        self.prev = None
        self.next = None


from collections import OrderedDict


class IndexedList:
    def __init__(self):
        self.ordered_dict = OrderedDict()
        self.order_list = []

    def insert_at_index(self, index, key, value):
        if index < 0 or index > len(self.order_list):
            raise IndexError("Index out of bounds")

        self.ordered_dict[key] = value
        self.order_list.insert(index, key)

    def insert_after(self, key, new_key, new_value):
        if key is None:
            # Insert at the beginning
            self.ordered_dict[new_key] = new_value
        elif key in self.ordered_dict:
            # Insert after the specified key
            items = list(self.ordered_dict.items())
            index = next((i for i, (k, v) in enumerate(items) if k == key), -1)
            if index != -1:
                items.insert(index + 1, (new_key, new_value))
                self.ordered_dict = OrderedDict(items)
            else:
                raise KeyError(f"Key '{key}' not found in the indexed list")
        else:
            raise KeyError(f"Key '{key}' not found in the indexed list")

    def display(self):
        for key, value in self.ordered_dict.items():
            print(f"({key}: {value})", end=" ")
        print()


# Example Usage:
indexed_list = IndexedList()
indexed_list.insert_at_index(0, "a", 1)
indexed_list.insert_at_index(1, "b", 2)
indexed_list.insert_at_index(1, "c", 3)
indexed_list.display()  # Output: (a: 1) (c: 3) (b: 2)

indexed_list.insert_at_index(2, "d", 4)
indexed_list.display()  # Output: (a: 1) (c: 3) (d: 4) (b: 2)
