import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import copy
import os
import time
import argparse
import yaml

import AGENT
import RESULT


class simulation:

    def __init__(self):

        # Get yaml parameter
        parser = argparse.ArgumentParser()
        parser.add_argument('yaml_file')
        args = parser.parse_args()

        with open(args.yaml_file, 'rt') as fh:
            self.yaml_parameters = yaml.safe_load(fh)

        # Initialize simulation parameters
        self.name_of_simulation = self.yaml_parameters['name_of_simulation']
        self.path = self.name_of_simulation
        self.size_world = self.yaml_parameters['resolution']
        self.size_world_real = self.yaml_parameters['size_world']
        self.scaling = self.size_world[0] / self.size_world_real[0]

        if self.size_world[0] / self.size_world_real[0] != self.size_world[1] / self.size_world_real[1]:
            print ('size_world and resolution need to have the same aspect ratio')

        else:
            # Initialize parameter_position
            position_initial = self.yaml_parameters['position_initial']
            for i in range(len(position_initial)):
                position_initial[i] = [int(position_initial[i][0] * self.scaling), int(position_initial[i][1] * self.scaling)]
            self.position_initial = position_initial

            # Initialize cicle dependent parameters
            self.performance_position_target = []
            self.performance_number_of_iteration = []
            self.performance_time_computation = []
            self.performance_time_picture = []
            self.cicle = 0

            # Make directories
            os.makedirs(self.path, exist_ok=True)
            os.makedirs(self.path + '/video', exist_ok=True)
            os.makedirs(self.path + '/sensor', exist_ok=True)
            os.makedirs(self.path + '/performance', exist_ok=True)

    def run(self):

        if self.yaml_parameters['position_target'] == 'random':
            self.position_target = [np.random.randint(self.size_world_real[0]), np.random.randint(self.size_world_real[1])]
        else:
            self.position_target = self.yaml_parameters['position_target']
        self.position_target = [int(self.position_target[0] * self.scaling), int(self.position_target[1] * self.scaling)]

        # Initialize performance_time vector
        self.time_computation = 0
        self.time_picture = 0

        # Initialize decision rate parameter
        self.d = self.yaml_parameters['deciding_rate']

        # Name accordingly to cicle
        self.name_of_simulation = self.path + '_' + str(self.cicle)

        # Initialize each robot
        self.my_robot = [0] * len(self.position_initial)
        self.my_decision = [0] * len(self.position_initial)
        for x in range(len(self.position_initial)):
            self.my_robot[x] = AGENT.bluefin(self.path, self.size_world, self.size_world_real, self.position_target, len(self.position_initial), x, self.position_initial)

        # Initialize the homebase
        self.my_homebase = AGENT.homebase(self.path, self.size_world, self.size_world_real, self.position_target, len(self.position_initial), self.position_initial)

        # Fill in position vectors
        for x in range(len(self.my_robot)):
            for y in range(len(self.my_robot)):
                self.my_robot[x].position_robot_exact[y] = self.my_robot[y].position_robot_exact[y]
                self.my_robot[x].position_robot_estimate[y] = self.my_robot[y].position_robot_estimate[y]

        # Initialize belief_position
        for x in range(len(self.position_initial)):
            for y in range(len(self.position_initial)):
                if x != y:
                    self.my_robot[x].my_belief_position.initialize_neighbour(y, self.my_robot[y].my_belief_position.belief_state[y])

        # Initialize the common result
        self.my_result = RESULT.result(self.path, self.name_of_simulation, self.size_world, self.size_world_real, self.position_target, self.my_robot, self.my_homebase)

        # Save picture of sensor_model (from the first robot), they are all the same
        self.my_robot[0].my_sensor_target.picture_save()
        self.my_robot[0].my_sensor_motion.picture_save()
        self.my_robot[0].my_sensor_distance.picture_save()

        # Save picture of the initial belief_state
        self.my_result.picture_save()

        # Find maximum in belief_state to know when the search is over
        belief_maximum = [0] * len(self.my_robot)
        for x in range(len(self.my_robot)):
            belief_maximum[x] = np.max(self.my_robot[x].my_belief_target.belief_state)

        # Looking for target until belief_state is accurate enough or runtime max is reached
        i = 0
        max_belief = self.yaml_parameters['max_belief'] / (self.size_world[0] * self.size_world[1])

        if self.yaml_parameters['max_runtime'] == '':
            max_runtime = self.my_robot[-1].range / (self.yaml_parameters['step_distance'] * self.yaml_parameters['deciding_rate'])
        else:
            max_runtime = self.yaml_parameters['max_runtime'] * self.scaling

        while (np.max(belief_maximum) < max_belief) & (i < max_runtime):

            # Start time for performance_time
            self.time_start = time.time()

            # Find new maximum in belief state to check if I'm certain enough about position of target
            belief_maximum = [0] * len(self.my_robot)
            for x in range(len(self.my_robot)):
                belief_maximum[x] = np.max(self.my_robot[x].my_belief_target.belief_state)

            # Update all position estimates based on my belief
            for x in range(len(self.my_robot)):
                self.my_robot[x].update_estimate_robot()
                self.my_robot[x].update_estimate_neighbour()

            # Deside where to go next, go there and update my beliefs accordingly
            if self.d >= self.yaml_parameters['deciding_rate']:
                self.d = 1
                angle_step_distance = [0] * len(self.my_robot)
                for x in range(len(self.my_robot)):
                    # Decide on next position
                    if self.yaml_parameters['decision'] == 'cheap':
                        angle_step_distance[x] = self.my_robot[x].my_decision.decide_cheap()
                    if self.yaml_parameters['decision'] == 'expensive':
                        angle_step_distance[x] = self.my_robot[x].my_decision.decide_expensive()
                    if self.yaml_parameters['decision'] == 'lawnmower':
                        angle_step_distance[x] = self.my_robot[x].my_decision.decide_lawnmower()

            else:
                self.d = self.d + 1

            for x in range(len(self.my_robot)):
                # Actually changing the position
                self.my_robot[x].update_exact(angle_step_distance[x])

                # Update exact position on each robot about the others for sensors
                for y in range(len(self.my_robot)):
                    self.my_robot[y].position_robot_exact[x] = copy.deepcopy(self.my_robot[x].position_robot_exact[x])

            for x in range(len(self.my_robot)):
                # Update belief about my position
                self.my_robot[x].my_belief_position.update_robot(angle_step_distance[x])

                # Update position estimate of myself
                self.my_robot[x].update_estimate_robot()

                # Update belief about neighbours position
                self.my_robot[x].my_belief_position.update_neighbour()

                # Update estimated position of neighbours based on belief_position
                self.my_robot[x].update_estimate_neighbour()

                # Update belief_target
                self.my_robot[x].my_belief_target.update(self.my_robot[x].position_robot_estimate[x])

            # Update homebase_belief_state
            self.my_homebase.my_belief_position.update()

            #if self.d >= self.yaml_parameters['deciding_rate']:
            # Exchange belief if close enough
            distance_estimate = [[1 for i in range(len(self.my_robot))] for j in range(len(self.my_robot))]
            distance_exact = [[1 for i in range(len(self.my_robot))] for j in range(len(self.my_robot))]

            for x in range(len(self.my_robot)):
                for y in range(len(self.my_robot)):

                    # I don't have to look how far away I am from myself
                    if (x != y):

                        # Do I think we are close enough, does my neighbour think that too & are we actually close enough & isn't he rising to the surface?
                        distance_estimate[x][y] = self.my_robot[x].my_belief_position.belief_state[y][1][0]
                        distance_exact[x][y] = np.sqrt((self.my_robot[x].position_robot_exact[x][0] - self.my_robot[x].position_robot_exact[y][0]) ** 2 + (self.my_robot[x].position_robot_exact[x][1] - self.my_robot[x].position_robot_exact[y][1]) ** 2)

                        if (distance_estimate[x][y] < self.my_robot[x].communication_range_observation) & (distance_exact[x][y] < self.my_robot[x].communication_range_observation) & (self.my_robot[y].id_contact[-1][0] == 0):
                            self.my_robot[x].id_contact[y][0] = 1
                            self.my_robot[y].id_contact[x][1] = 1

                            # Update the position estimate of my neighbour about me
                            self.my_robot[y].my_belief_position.initialize_neighbour(x, self.my_robot[x].my_belief_position.belief_state[x])

                            # Merge all the logs, if they contain more information than I already know
                            for z in range(len(self.my_robot)):
                                if len(self.my_robot[x].my_belief_target.position_log_estimate[z]) < len(self.my_robot[y].my_belief_target.position_log_estimate[z]):
                                    self.my_robot[x].my_belief_target.merge(z, self.my_robot[y].my_belief_target.position_log_estimate[z], self.my_robot[y].my_belief_target.observation_log[z])

                        # If they are not close enough to communicate, they don't have contact
                        else:
                            self.my_robot[x].id_contact[y][0] = 0
                            self.my_robot[y].id_contact[x][1] = 0

            for x in range(len(self.my_robot)):
                if self.my_robot[x].id_contact[-1][0] == self.my_robot[x].my_decision.diving_depth:
                    for z in range(len(self.my_robot)):

                        # Reset all connections
                        if x != z:
                            self.my_robot[x].id_contact[z][0] = 0
                            self.my_robot[z].id_contact[x][1] = 0

                        # Update homebase about target
                        if len(self.my_homebase.my_belief_target.position_log_estimate[z]) < len(self.my_robot[x].my_belief_target.position_log_estimate[z]):
                            self.my_homebase.my_belief_target.merge(z, self.my_robot[x].my_belief_target.position_log_estimate[z], self.my_robot[x].my_belief_target.observation_log[z])

                        # Update homebase about position
                        self.my_robot[x].my_belief_position.surface()
                        self.my_robot[x].update_estimate_robot()
                        self.my_homebase.my_belief_position.belief_state[x] = copy.deepcopy(self.my_robot[x].my_belief_position.belief_state[x])

            for x in range(len(self.my_robot)):
                if self.my_robot[x].id_contact[-1][0] == self.my_robot[x].my_decision.diving_depth:
                    for z in range(len(self.my_robot)):

                        # Update robots about target
                        if len(self.my_robot[x].my_belief_target.position_log_estimate[z]) < len(self.my_homebase.my_belief_target.position_log_estimate[z]):
                            self.my_robot[x].my_belief_target.merge(z, self.my_homebase.my_belief_target.position_log_estimate[z], self.my_homebase.my_belief_target.observation_log[z])

                    # Update the position estimate of my neighbour about me
                    for y in range(len(self.my_robot)):
                        if x != y:
                            self.my_robot[y].my_belief_position.initialize_neighbour(x, self.my_robot[x].my_belief_position.belief_state[x])

            # Increase runtime counter
            i = i + self.my_robot[-1].step_distance

            # How long it takes to compute everything
            self.time_computation = self.time_computation + (time.time() - self.time_start)

            if self.d >= self.yaml_parameters['deciding_rate']:
                # Safe picture of the beliefs (target & position) only everytime i take a picture
                self.my_result.picture_save()

            # How long it takes to save a picture
            self.time_picture = self.time_picture + (time.time() - self.time_start)

        # Turn saved pictures into video and then delete the pictures
        self.my_result.video_save()

        # Update cicle dependent parameters
        self.cicle = self.cicle + 1

        self.performance_position_target = self.performance_position_target + [self.position_target]
        self.performance_number_of_iteration = self.performance_number_of_iteration + [self.my_result.picture_id]

        self.performance_time_computation = self.performance_time_computation + [self.time_computation / (i + 1)]
        self.performance_time_picture = self.performance_time_picture + [self.time_picture / (i + 1)]

    def performance_target_position(self):
        # Initializing performance_map
        performance_map = [[0 for i in range(self.size_world[0])] for j in range(self.size_world[1])]

        # Filling performance_map
        for i in range(len(self.performance_position_target)):
            performance_map[self.performance_position_target[i][1]][self.performance_position_target[i][0]] = self.performance_number_of_iteration[i]

        # Creating visual representation of performance_map
        plt.imshow(performance_map, extent=[0,self.size_world_real[0],self.size_world_real[1],0])
        plt.colorbar()
        plt.title('Performance analysis ' + '(' + str(len(self.position_initial)) + ' robots)' + '\n' + 'Average: ' + str(np.sum(self.performance_number_of_iteration) / self.cicle))

        # Save picture in main folder
        plt.savefig(self.path + '/performance/' + self.path + '_performance_target_position.png')
        plt.close()


    def performance_time(self):
        # Creating visual representation of time results
        i_x = np.linspace(1, self.cicle, self.cicle)
        plt.plot(i_x, self.performance_time_computation)
        plt.plot(i_x, self.performance_time_picture)
        plt.plot(i_x, np.subtract(self.performance_time_picture, self.performance_time_computation))

        title_picture = 'Average picture: ' + str(np.sum(self.performance_time_picture) / self.cicle)
        title_computation = 'Average computation: ' + str(np.sum(self.performance_time_computation) / self.cicle)
        title_difference = 'Average difference: ' + str(np.sum(np.subtract(self.performance_time_picture, self.performance_time_computation)) / self.cicle)

        plt.title('Performance analysis ' + '(' + str(len(self.position_initial)) + ' robots)')
        plt.legend([title_computation, title_picture, title_difference])

        # Save picture in main folder
        plt.savefig(self.path + '/performance/' + self.path + '_performance_time.png')
        plt.close()

# Initialize a simulation
my_simulation = simulation()

for i in range(1000):
    # Everytime I set a new random position for the target
    my_simulation.run()

    # Get information of performance over the total of all my simulations
    my_simulation.performance_target_position()
    my_simulation.performance_time()