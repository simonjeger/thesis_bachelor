# This is a script that reads out the data generated by SIMULATION.py

import numpy as np
import matplotlib.pyplot as plt
from scipy.interpolate import griddata
import os

def read(f):
    line = f.readline()
    position_target_x = []
    position_target_y = []
    performance_number = []
    count_line = 0

    while line:
        i = 0
        for word in line.split():
            if i == 0:
                position_target_x = position_target_x + [float(word)]
            if i == 1:
                position_target_y = position_target_y + [float(word)]
            if i == 2:
                performance_number = performance_number + [float(word)]
            i = i + 1
        count_line = count_line + 1
        line = f.readline()
    print('number of lines in this file: ' + str(count_line))
    f.close()
    return [position_target_x, position_target_y, performance_number]

def build_histogram(performance_number, n, bins_n, file, path, color):
    # Plot specific stuff
    mean = []
    std = []

    for t in range(100):
        mean_inter = []
        std_inter = []

        for x in performance_number:
            mean_inter.append(np.sum(x[t*n:t*n+n])/n)
            std_inter.append(np.sqrt(1/(n-1)*np.sum(np.subtract(x[t*n:t*n+n], np.sum(x[t*n:t*n+n])/n)**2)))

        # Calculating statistical moments
        mean.append(mean_inter)
        std.append(std_inter)

    mean = np.array(mean)

    # Labels
    label = []
    for f in file:
        label.append(os.path.basename(f.name)[0:26])

    # Generating plot
    if len(color) == 0:
        plt.hist(mean, bins=np.linspace(np.min(mean), np.max(mean) + (np.max(mean) - np.min(mean)) / bins_n, bins_n), label=label)
    else:
        plt.hist(mean, bins=np.linspace(np.min(mean), np.max(mean) + (np.max(mean) - np.min(mean)) / bins_n, bins_n),label=label, color=color)

    # Adding legend
    plt.legend(loc='best')
    plt.xlabel('time till target found [s]')

    # Calculating overall mean
    mean_mean = [0]*len(mean[-1])
    mean_std = [0]*len(mean[-1])
    for j in range(len(mean)):
        for i in range(len(mean[j])):
            mean_mean[i] = mean_mean[i] + mean[j][i]
            mean_std[i] = mean_std[i] + std[j][i]
    mean_mean = np.divide(mean_mean, len(mean))
    mean_std = np.divide(mean_std, len(std))

    print('mean(MTTF): ' + str(mean_mean))
    plt.title('mean(MTTF): ' + str(np.round(mean_mean, 3)) + ' h' + '\n' + 'std(MTTF):     ' + str(np.round(mean_std, 3)) + ' h')
    plt.xlim(0, 75)
    plt.ylim(0, 40)
    plt.savefig(path + 'histogram.pdf')
    plt.close()

def build_map(performance_number, n, file, path):
    mean = []
    comparison = []

    for t in range(100):
        mean_inter = []

        for x in performance_number:
            mean_inter.append(np.sum(x[t*n:t*n+n])/n)

        # Calculating statistical moments
        mean.append(mean_inter)
        comparison.append(np.divide(mean_inter[0], mean_inter[1]))

    # Generate map
    z = [[0 for i in range(10)] for j in range(10)]
    for i in range(len(comparison)):
        z[i%10][int(i/10)] = comparison[i]

    # Change into numpy array (otherwise I get an error)
    z = np.array(z)

    # Calculating overall mean
    mean_mean = [0] * len(mean[-1])
    for j in range(len(mean)):
        for i in range(len(mean[j])):
            mean_mean[i] = mean_mean[i] + mean[j][i]
    mean_mean = np.divide(mean_mean, len(mean))

    # Labels
    label = []
    for f in file:
        label.append(os.path.basename(f.name)[0:26])

    # Generating plot
    plt.title(label[0] + ': '+ str(np.round(mean_mean[0],3)) + ' h' + '\n' + label[1] + ': ' + str(np.round(mean_mean[1],3)) + ' h')
    plt.imshow(z, vmin=0, vmax=2)
    plt.colorbar()

    plt.savefig(path + 'map.pdf')
    plt.close()

path = 'data/'

name = []
'''name = ['R_1rob_8dir_1pat_exp_off_1_performance_target_position.txt',
        'R_1rob_8dir_2pat_exp_off_1_performance_target_position.txt',
        'R_1rob_8dir_3pat_exp_off_1_performance_target_position.txt']'''
'''name = ['R_1rob_8dir_1pat_che_off_1_performance_target_position.txt',
        'R_1rob_8dir_2pat_che_off_1_performance_target_position.txt',
        'R_1rob_8dir_3pat_che_off_1_performance_target_position.txt']'''
'''name = ['R_1rob_8dir_1pat_che_off_1_performance_target_position.txt',
        'R_2rob_8dir_1pat_che_on_2_performance_target_position.txt',
        'R_3rob_8dir_1pat_che_on_2_performance_target_position.txt']'''

color = []
#color = ['gold', 'yellow', 'lemonchiffon']
#color = ['firebrick', 'darksalmon', 'mistyrose']
#color = ['royalblue', 'lightskyblue', 'lightsteelblue']
file = []

if len(name) == 0:
    for i in os.listdir(path):
        if i.endswith('.txt'):
            file.append(open(path + i, "r"))

else:
    for i in name:
        file.append(open(path + i, "r"))

performance_number = []
for f in file:
    performance_number.append(read(f)[2])

build_histogram(performance_number, 5, 15, file, path, color)
build_map([performance_number[0], performance_number[1]], 5, file, path)