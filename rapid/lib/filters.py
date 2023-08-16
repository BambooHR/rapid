from typing import List


def attribute_value_filter(attr: str, value: any):
    def check(check_obj):
        return hasattr(check_obj, attr) and getattr(check_obj, attr) == value
    return check


class ObjectFilters:


    @staticmethod
    def by_attribute(attr: str, value: str, arr: List[object]):
        return list(filter(attribute_value_filter(attr, value), arr))

