def custom_sort_bug_count_dict_by_count_creation_time(item):
    return item[1], item[0].creation_time


class DictUtil:

    @staticmethod
    def sort_bug_count_dict_by_count_creation_time(my_dict, key=custom_sort_bug_count_dict_by_count_creation_time, reverse=True):
        sorted_dict = dict(sorted(my_dict.items(), key=key, reverse=reverse))
        return sorted_dict

    @staticmethod
    def to_dict(one_object):
        """
        Returns a dictionary representation of the AutonomicTask instance.
        """
        return {k: v for k, v in one_object.__dict__.items()}

    @staticmethod
    def from_dict(one_dict):
        """
        Set attributes values by the given dict_obj
        Args:
            one_dict (dict): The dict with attributes and values
        """
        for key, value in one_dict.items():
            if hasattr(one_dict, key):
                setattr(one_dict, key, value)

    @staticmethod
    def remove_keys(obj, keys_to_remove):
        """
        Recursively remove certain keys from a nested dict or list of dicts.

        :param obj: the data structure (dict, list, or any other type)
        :param keys_to_remove: a set or list of keys to remove
        :return: a new copy of 'obj' with the specified keys removed
        """
        if isinstance(obj, dict):
            # For a dictionary, build a new dict:
            # - Skip any keys in keys_to_remove
            # - Recursively process the value
            return {
                k: DictUtil.remove_keys(v, keys_to_remove)
                for k, v in obj.items()
                if k not in keys_to_remove
            }
        elif isinstance(obj, list):
            # For a list, apply remove_keys to each item
            return [DictUtil.remove_keys(item, keys_to_remove) for item in obj]
        else:
            # Base case: obj is not a dict or list; return it as-is
            return obj

