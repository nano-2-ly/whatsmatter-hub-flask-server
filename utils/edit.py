
def deleteItem(data, target_key, target_value):
    filtered_dict_list = [item for item in data if item.get(target_key) != target_value]   

    return filtered_dict_list


def putItem(data, target_key, target_value, new_item):
    filtered_dict_list = [item for item in data if item.get(target_key) != target_value]   
    filtered_dict_list.append(new_item)
    return filtered_dict_list