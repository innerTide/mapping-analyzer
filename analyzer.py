# This is a mapping analysis script for constrained mapping.
import copy
import re

import matplotlib.pyplot as plt
import numpy as np

# Load the neural connection groups.
# This procedure generates a list of connection groups.
# Indexed by Connection Group ID
# IDs of Neural Nodes are listed in each item

TDM_DELAY_UNIT = 1
SWITCH_DELAY_UNIT = 5
SWITCH_POWER_UNIT = 2

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

# Load the architectural connections.
# This procedure generated bus connection.
# Indexed by Bus ID
# Computational Nodes connected to the bus are listed
# in each item from left to right#

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

# Compute the mappable list and switch occupation.
# This generates the mappable bus list of each neural node.
# Indexed by Connection Group ID.
# All the mappable buses are listed in the item as Bus ID.
# Switch occupation is corresponding to the mapping#

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


# Compute all the possible mappings.
# Each item of the generated list is also a list
# The list is indexed by Connection Group ID
# And the item is the mapped Bus ID
# There is a hint for the following students.
# When doing list operations,
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

# Generate the TDM number.
# Each item is also a list corresponding to Mapping List
# Items are indexed by Connection Group ID
# the number is anticipated TDM count #
tdm_number_list = []
for mapping_item in mapping_list:
    tdm_number_item = []
    for con_id in range(len(mapping_item)):
        tdm_count = 0
        bus_id = mapping_item[con_id]
        for i in mapping_item:
            if i == bus_id:
                temp_con_id = mapping_item.index(i)
                if len(set(connection_group_list[temp_con_id]) &
                       set(connection_group_list[con_id])) != 0:
                    tdm_count += 1
        tdm_count = tdm_count - 1
        tdm_number_item.append(tdm_count)
    tdm_number_list.append(tdm_number_item)

print('TDM table:')
print(tdm_number_list)


# Compute the delay and power consumption of each mapping. #
power_consumption_list = []
delay_list = []
for mapping_item in mapping_list:
    mapping_switch_delay_dict = {}
    total_delay = 0
    mapping_switch_occupation = 0
    for con_id in range(len(mapping_item)):
        bus_id = mapping_item[con_id]
        occupation_temp = switch_occupation[con_id][mappable_list[con_id].index(bus_id)]

        # The number of connection group mapped on the bus
        # will affect the number of TDM
        # tdm_factor = len(mapping_item) - len(set(mapping_item))
        tdm_delay_temp = tdm_number_list[mapping_list.index(mapping_item)][con_id] ** 2
        delay_temp = occupation_temp*SWITCH_DELAY_UNIT + tdm_delay_temp*TDM_DELAY_UNIT
        if bus_id in mapping_switch_delay_dict:
            if delay_temp > mapping_switch_delay_dict[bus_id]:
                mapping_switch_delay_dict[bus_id] = delay_temp
        else:
            mapping_switch_delay_dict[bus_id] = delay_temp
        mapping_switch_occupation += occupation_temp
    # tdm_number = len(mapping_item) - len(set(mapping_item))
    power_consumption = mapping_switch_occupation * SWITCH_POWER_UNIT
    for i in mapping_switch_delay_dict:
        total_delay += mapping_switch_delay_dict[i]
    print("Info for mapping %d" % mapping_list.index(mapping_item))
    print("Power consumption: %d" % power_consumption)
    print("Anticipated delay: %d" % total_delay)
    power_consumption_list.append(power_consumption)
    delay_list.append(total_delay)


# Plotting the result with scatter figure
x = np.array(delay_list)
y = np.array(power_consumption_list)
dot_label = {}
plt.scatter(x, y)
plt.xlabel('Delay (clock cycles)')
plt.ylabel('Power consumption (energy unit)')
for i in range(len(delay_list)):
    if (x[i], y[i]) not in dot_label:
        dot_label[(x[i], y[i])] = str(i)
    else:
        dot_label[(x[i], y[i])] = dot_label[(x[i], y[i])]\
                                  + ', ' + str(i)
    for dot in dot_label:
        plt.annotate(dot_label[dot], dot)
plt.show()

