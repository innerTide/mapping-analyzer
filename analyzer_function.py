import copy
import re

from mpl_toolkits.mplot3d import Axes3D
import matplotlib.pyplot as plt
import numpy as np
import sys
import tkinter.filedialog
import tkinter.messagebox

TDM_DELAY_UNIT = 5
SWITCH_DELAY_UNIT = 1
SWITCH_POWER_UNIT = 1
SWITCH_AREA_UNIT = 1
MODE = 'avg'
VERBOSE = False


def calculation(connection_file_name, bus_file_name):
    connection_file = open(connection_file_name, mode='r')
    connection_str = connection_file.read()
    connection_re = re.compile('([0-9]+,)+[0-9]+', flags=0)
    connection_group_iter = connection_re.finditer(connection_str)
    connection_group_list = []

    for connection_group_iter_i in connection_group_iter:
        connection_group = list(map(int, connection_group_iter_i.group().split(',')))
        connection_group_list.append(connection_group)

    print("Neural connection groups:")
    print(connection_group_list)

    connection_file.close()

    # Load the architectural connections.
    # This procedure generated bus connection.
    # Indexed by Bus ID
    # Computational Nodes connected to the bus are listed
    # in each item from left to right#

    bus_file = open(bus_file_name, mode='r')
    bus_str = bus_file.read()
    bus_re = re.compile('([0-9]+,)+[0-9]+', flags=0)
    bus_iter = bus_re.finditer(bus_str)
    bus_list = []

    for bus_iter_i in bus_iter:
        bus_arch = list(map(int, bus_iter_i.group().split(',')))
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
            if set(connection_group_list[con_id]) \
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
                occupation.append(max_place - min_place + 1)

        if len(mappable) == 0:
            print("ERROR, a connection group cannot be mapped!!!")
            print(connection_group_list[con_id])
            sys.exit(1)

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
            for temp_bus_id in mappable_list[con_id]:
                mapping_list.append([temp_bus_id])
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
            for mapping_item_i in mapping_item:
                if mapping_item_i == bus_id:
                    temp_con_id = mapping_item.index(mapping_item_i)
                    if len(set(connection_group_list[temp_con_id]) &
                                   set(connection_group_list[con_id])) != 0:
                        tdm_count += 1
            tdm_count = tdm_count
            tdm_number_item.append(tdm_count)
        tdm_number_list.append(tdm_number_item)

    print('TDM table:')
    print(tdm_number_list)

    # Compute the delay and power consumption of each mapping. #
    power_consumption_list = []
    delay_list = []
    switch_usage_list = []
    # total_tdm_list = []
    # max_delay_list = []
    for mapping_item in mapping_list:
        mapping_switch_delay_dict = {}
        mapping_switch_occupation = 0
        for con_id in range(len(mapping_item)):
            bus_id = mapping_item[con_id]
            occupation_temp = switch_occupation[con_id][mappable_list[con_id].index(bus_id)]

            # The number of connection group mapped on the bus
            # will affect the number of TDM
            # tdm_factor = len(mapping_item) - len(set(mapping_item))
            tdm_delay_temp = tdm_number_list[mapping_list.index(mapping_item)][con_id]
            delay_temp = occupation_temp * SWITCH_DELAY_UNIT + tdm_delay_temp * TDM_DELAY_UNIT
            if bus_id in mapping_switch_delay_dict:
                if MODE == 'avg':
                    mapping_switch_delay_dict[bus_id] += delay_temp
                elif MODE == 'min':
                    if delay_temp < mapping_switch_delay_dict[bus_id]:
                        mapping_switch_delay_dict[bus_id] = delay_temp
                else:
                    if delay_temp > mapping_switch_delay_dict[bus_id]:
                        mapping_switch_delay_dict[bus_id] = delay_temp
            else:
                mapping_switch_delay_dict[bus_id] = delay_temp
            mapping_switch_occupation += occupation_temp

        # tdm_number = len(mapping_item) - len(set(mapping_item))
        power_consumption = mapping_switch_occupation * SWITCH_POWER_UNIT
        computed_delay = 0

        if MODE == 'avg':
            for mapping_switch_delay_dict_i in mapping_switch_delay_dict:
                computed_delay += (mapping_switch_delay_dict[mapping_switch_delay_dict_i]
                                   / mapping_item.count(mapping_switch_delay_dict_i))
            computed_delay = computed_delay * 1.0 / float(len(mapping_switch_delay_dict))
        elif MODE == 'min':
            is_first = True
            for mapping_switch_delay_dict_i in mapping_switch_delay_dict:
                if is_first:
                    computed_delay = mapping_switch_delay_dict[mapping_switch_delay_dict_i]
                    is_first = False
                else:
                    if mapping_switch_delay_dict[mapping_switch_delay_dict_i] < computed_delay:
                        computed_delay = mapping_switch_delay_dict[mapping_switch_delay_dict_i]
        else:
            for mapping_switch_delay_dict_i in mapping_switch_delay_dict:
                if mapping_switch_delay_dict[mapping_switch_delay_dict_i] > computed_delay:
                    computed_delay = mapping_switch_delay_dict[mapping_switch_delay_dict_i]

        switch_usage = 0
        for mapping_item_i in set(mapping_item):
            switch_usage += len(bus_list[mapping_item_i]) * SWITCH_AREA_UNIT

        if VERBOSE:
            print("Info for mapping %d" % mapping_list.index(mapping_item))
            print("Power consumption: %d" % power_consumption)
            print("Computed delay: %f" % computed_delay)
            print("Switch usage: %d" % switch_usage)
        power_consumption_list.append(power_consumption)
        delay_list.append(computed_delay)
        switch_usage_list.append(switch_usage)

    # for tdm_number_item in tdm_number_list:
    #     total_tdm_list.append(max(tdm_number_item))
    return delay_list, power_consumption_list, switch_usage_list


# Plotting the result with scatter figure
main_window = tkinter.Tk()
# main_window.withdraw()
connection_group_file_name = tkinter.filedialog.askopenfilename(title='Connection group file', initialdir='.')
bus_file_list = list(tkinter.filedialog.askopenfilenames(title='Bus architecture file(s)', initialdir='.'))
print(bus_file_list)

if connection_group_file_name == '' or bus_file_list == []:
    tkinter.messagebox.showerror(title='Error!', message='Error loading the configuration file!')
    sys.exit(10)

if len(bus_file_list) > 5:
    tkinter.messagebox.showerror(title="Exceeding limitation:",
                                 message="More than 5 architecture files are selected!")
    sys.exit(100)

main_window.quit()
main_window.destroy()
# bus_file_list = ['bus-arch-0.conf',
#                  'bus-arch-1.conf',
#                  'bus-arch-2.conf']
color_list = ['m', 'c', 'r', 'g', 'b']
symbol_list = ['x', '+', '^', 'o', '8']
size_list = [20, 17, 14, 11, 8]
x = []
y = []
z = []
# fig_size = matplotlib.pyplot.gcf()
# fig_size.set_size_inches(50, 50)
fig = plt.figure(0)
for i, file_name in enumerate(bus_file_list):
    x, y, z = calculation(connection_group_file_name, file_name)
    plt.subplot(121)
    plt.xlabel('Delay (time unit)')
    plt.ylabel('Power consumption (power unit)')

    x = np.array(x)
    y = np.array(y)

    plt.scatter(x, y, marker=symbol_list[i], color=color_list[i],
                label='Arch ' + str(i), s=size_list[i])

    plt.subplot(122)
    z = np.array(z)
    plt.xlabel('Area (square unit)')
    plt.ylabel('Power consumption (time unit)')
    plt.scatter(z, y, marker=symbol_list[i], color=color_list[i],
                label='Arch ' + str(i), s=size_list[i])
    plt.legend(loc='upper right')

    # if max(x) > xlim:
    #     xlim = max(x)

    # dot_label = {}
    # for i in range(len(y)):
    #     if (x[i], y[i]) not in dot_label:
    #         dot_label[(x[i], y[i])] = str(i)
    #         # else:
    #         #     dot_label[(x[i], y[i])] = dot_label[(x[i], y[i])]\
    #         #                               + ', ' + str(i)
    # for dot in dot_label:
    #     plt.annotate(dot_label[dot], dot)

plt.savefig('result_' + MODE, dpi=600)
plt.show()

# Plotting the 3D figure
fig_3d = plt.figure(1)
ax = fig_3d.add_subplot(111, projection='3d')
for i, file_name in enumerate(bus_file_list):
    ax.scatter(x, y, z, c=color_list[i], marker=symbol_list[i], s=size_list[i])

ax.set_xlabel('Delay (time unit)')
ax.set_ylabel('Power consumption (power unit)')
ax.set_zlabel('Area (square unit)')

plt.savefig('result_3d_' + MODE, dpi=600)
plt.show()
