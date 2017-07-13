# This is a mapping analysis script for constrained mapping.#
import copy
import re

# Load the neural connection groups.#

connection_file = open('connection-group.conf', mode='r')
connection_str = connection_file.read()
connection_re = re.compile('([0-9]+,)+[0-9]+', flags=0)
connection_group_iter = connection_re.finditer(connection_str)
connection_group_list = []

for i in connection_group_iter:
    connection_group = list(map(int, i.group().split(',')))
    connection_group_list.append(connection_group)

print("Neural connection groups:")
print(connection_group_list)

connection_file.close()

# Load the architectural connections. #

bus_file = open('bus-arch.conf', mode='r')
bus_str = bus_file.read()
bus_re = re.compile('([0-9]+,)+[0-9]+', flags=0)
bus_iter = bus_re.finditer(bus_str)
bus_list = []

for i in bus_iter:
    bus_arch = list(map(int, i.group().split(',')))
    bus_list.append(bus_arch)

print("Bus connections:")
print(bus_list)

bus_file.close()

# Compute the mappable list and switch occupation. #

mappable_list = []
switch_occupation = []
for con_id in range(len(connection_group_list)):
    mappable = []
    occupation = []
    for bus_id in range(len(bus_list)):
        if set(connection_group_list[con_id])\
               .issubset(set(bus_list[bus_id])):
            mappable.append(bus_id)
            max_place = 0
            min_place = len(bus_list[bus_id])
            for node in connection_group_list[con_id]:
                placement = bus_list[bus_id].index(node)
                if placement > max_place:
                    max_place = placement
                if placement < min_place:
                    min_place = placement
            occupation.append(max_place-min_place+1)
    mappable_list.append(mappable)
    switch_occupation.append(occupation)

print("All mappable buses of each connection group:")
print(mappable_list)
print("Switch occupation for each mapping:")
print(switch_occupation)


# Compute all the possible mappings. #
# There is a hint for the following students. #
# When doing list operations, #
# please distinguish "=" and "copy.copy(a)! "

mapping_list = []
for con_id in range(len(connection_group_list)):
    last_mapping = copy.copy(mapping_list)
    mapping_list = []
    if con_id == 0:
        mapping_list.append(mappable_list[con_id])
    else:
        for mapping in last_mapping:
            for bus_id in mappable_list[con_id]:
                next_mapping = copy.copy(mapping)
                next_mapping.append(bus_id)
                mapping_list.append(next_mapping)

print("All possible mappings, indexed by communication group ID"
      " and contented by bus ID: ")
print(mapping_list)


# Compute the delay and power consumption of each mapping. #
for mapping_item in mapping_list:
    mapping_switch_delay_dict = {}
    mapping_switch_delay = 0
    mapping_switch_occupation = 0
    for con_id in range(len(mapping_item)):
        bus_id = mapping_item[con_id]
        # print(switch_occupation[con_id][mappable_list[con_id].index(bus_id)])
        occupation_temp = switch_occupation[con_id][mappable_list[con_id].index(bus_id)]
        if bus_id in mapping_switch_delay_dict:
            if occupation_temp > mapping_switch_delay_dict[bus_id]:
                mapping_switch_delay_dict[bus_id] = occupation_temp
        else:
            mapping_switch_delay_dict[bus_id] = occupation_temp
        mapping_switch_occupation += occupation_temp
    tdm_number = len(mapping_item) - len(set(mapping_item))
    for i in mapping_switch_delay_dict:
        mapping_switch_delay += mapping_switch_delay_dict[i]
    print("Info for mapping %d" % mapping_list.index(mapping_item))
    print("Power consumption: %d" % mapping_switch_occupation)
    print("TDM: %d" % tdm_number)
    print("Switch occupation %d" % mapping_switch_delay)
    print(mapping_switch_delay_dict)
    