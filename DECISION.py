import numpy as np
import copy


class decision:

    def __init__(self, size_world, my_belief_target, my_belief_position, id_robot, id_contact, position_robot_estimate, my_sensor_target, path_depth, number_of_directions, step_distance):
        self.size_world = size_world
        self.my_belief_target = my_belief_target
        self.my_belief_position = my_belief_position
        self.position_robot_estimate = position_robot_estimate
        self.id_robot = id_robot
        self.id_contact = id_contact
        self.my_sensor_target = my_sensor_target

        # Parameters that determine the motion of the robot
        self.path_depth = path_depth
        self.number_of_directions = number_of_directions
        self.step_distance = step_distance
        self.step_angle = 2 * np.pi / self.number_of_directions

        # Parameters that determine when to rise to the surface
        self.diving_depth = 1


    def decide(self):
        # Am I on the same depth level as the rest
        if self.id_contact[-1][0] > 0:
            self.id_contact[-1][0] = self.id_contact[-1][0] - 1
            return [0, 0]

        else:
            # Update rise_gain
            weight_std_robot = self.my_belief_position.belief_state[self.id_robot][0][1]
            weight_target = np.max(self.my_belief_target.belief_state) * (self.size_world[0] * self.size_world[1])

            self.rise_gain = weight_std_robot / (2 * self.diving_depth)

            # Find out who is involved in the decision
            id_robot = []
            for x in range(len(self.id_contact) - 1):
                if self.id_contact[x][1] == 1:
                    id_robot = id_robot + [x]

            # Initialize all possible positions, according novelty lists and values
            position_observe = [[[0]]]
            novelty = [[0]]
            value = [[0]]
            for k in range(1, self.path_depth + 1):
                for j in range(0, len(id_robot)):
                    layer = (k - 1) * len(id_robot) + j + 1
                    position_observe = position_observe + [[[0, 0] for i in range((self.number_of_directions) ** (layer))]]

                    novelty = novelty + [[[[0] for i in range(layer - 1)] for j in range((self.number_of_directions) ** (layer))]]

                    value = value + [[0 for i in range((self.number_of_directions) ** (layer))]]

            # Determine start level
            for k in range(1, 2):
                for j in range(0, len(id_robot)):
                    layer = (k - 1) * len(id_robot) + j + 1

                    # Determine start position depending on which robot we are looking at
                    if id_robot[j] == self.id_robot:
                        position_start = copy.deepcopy(self.position_robot_estimate[id_robot[j]])
                    else:
                        dx = copy.deepcopy(self.position_robot_estimate[id_robot[j]][1] * np.cos(self.position_robot_estimate[id_robot[j]][0]))
                        dy = copy.deepcopy(self.position_robot_estimate[id_robot[j]][1] * np.sin(self.position_robot_estimate[id_robot[j]][0]))
                        position_start = [copy.deepcopy(self.position_robot_estimate[self.id_robot][0]) + dx, copy.deepcopy(self.position_robot_estimate[self.id_robot][1]) + dy]

                    # Fill the in the first depth level
                    for i in range((self.number_of_directions) ** layer):
                        p_x = position_start[0] + self.step_distance * np.cos((i % self.number_of_directions) * self.step_angle)
                        p_y = position_start[1] + self.step_distance * np.sin((i % self.number_of_directions) * self.step_angle)
                        position_observe[layer][i] = [p_x, p_y]

            # Fill in the deeper path tree
            for k in range(2, self.path_depth + 1):
                for j in range(0, len(id_robot)):
                    layer = (k - 1) * len(id_robot) + j + 1

                    # Fill the in the higher levels
                    for i in range((self.number_of_directions) ** layer):
                        p_x = position_observe[layer-len(id_robot)][int(i / ((self.number_of_directions) ** len(id_robot)))][0] + self.step_distance * np.cos((i % self.number_of_directions) * self.step_angle)
                        p_y = position_observe[layer-len(id_robot)][int(i / ((self.number_of_directions) ** len(id_robot)))][1] + self.step_distance * np.sin((i % self.number_of_directions) * self.step_angle)
                        position_observe[layer][i] = [p_x, p_y]

            # Fill in novelty tree
            for k in range(1, self.path_depth + 1):
                for j in range(0, len(id_robot)):
                    layer = (k - 1) * len(id_robot) + j + 1

                    # This concept doesn't make sense for the first layer
                    if layer > 1:
                        for i in range((self.number_of_directions) ** layer):
                            for n in range(0, len(novelty[layer][i])):
                                p_dx = position_observe[layer][i][0] - position_observe[layer-(n+1)][int(i / ((self.number_of_directions) ** (n+1)))][0]
                                p_dy = position_observe[layer][i][1] - position_observe[layer-(n+1)][int(i / ((self.number_of_directions) ** (n+1)))][1]
                                novelty[layer][i][n] = 1 - self.my_sensor_target.likelihood(np.sqrt(p_dx ** 2 + p_dy ** 2))

                            # Store normalised novelty weight in last value
                            novelty[layer][i][-1] = np.sum(novelty[layer][i]) / (len(novelty[layer][i]))

            # Fill in value tree
            for k in range(1, self.path_depth + 1):
                for j in range(len(id_robot)):
                    layer = (k - 1) * len(id_robot) + j + 1
                    for i in range((self.number_of_directions) ** layer):

                        # If path leads outside of world
                        if (position_observe[layer][i][0] < 0) | (position_observe[layer][i][0] >= self.size_world[0]) | (position_observe[layer][i][1] < 0) | (position_observe[layer][i][1] >= self.size_world[1]):
                            value[layer][i] = 0

                        # Rate every path through marginalisation
                        else:
                            x = np.linspace(0,self.size_world[0] - 1, self.size_world[0])
                            y = np.linspace(0, self.size_world[1] - 1, self.size_world[1])
                            xy = np.meshgrid(x,y)
                            distance = np.sqrt(np.subtract(xy[0], position_observe[layer][i][0])**2 + np.subtract(xy[1], position_observe[layer][i][1])**2)
                            weight_true = np.sum(np.multiply(self.my_sensor_target.likelihood(distance), self.my_belief_target.belief_state))
                            weight_false = 1 - weight_true

                            # In the first layer the novelty doesn't exist, so I set it do a default value with respect to its last know point
                            if layer == 1:
                                weight_novelty = 1 - self.my_sensor_target.likelihood(self.step_distance)

                            # After that it does
                            else:
                                weight_novelty = novelty[layer][i][-1]

                            # Filling in value tree
                            value[layer][i] = weight_novelty * (weight_true * self.kullback_leibler(self.my_belief_target.test_true(position_observe[layer][i]), self.my_belief_target.belief_state) + weight_false * self.kullback_leibler(self.my_belief_target.test_false(position_observe[layer][i]), self.my_belief_target.belief_state))

            # Sum up the value tree and store in last level
            for k in range(1, self.path_depth + 1):
                for j in range(len(id_robot)):
                    layer = (k - 1) * len(id_robot) + j + 1
                    for i in range((self.number_of_directions) ** layer):
                        value[layer][i] = value[layer][i] + value[layer-1][int(i / (self.number_of_directions))]

            # Rise to the surface or continue exploring
            layer_max = (self.path_depth - 1) * len(id_robot) + len(id_robot)

            #if np.max(value[-1]) / layer_max > self.rise_gain:
            if self.rise_gain < 1.2:
                # Choose path
                my_layer = (self.path_depth - 1) * len(id_robot) + len(id_robot) - id_robot.index(self.id_robot) - 1
                choice = int(np.argmax(value[-1]) / ((self.number_of_directions) ** my_layer)) % self.number_of_directions
                return [choice * self.step_angle, self.step_distance]
            else:
                # Choose to rise
                self.id_contact[-1][0] = 2 * self.diving_depth
                return [0, 0]


    def kullback_leibler(self, x, y):
        result = 0
        for i_y in range(0, self.size_world[1]):
            for i_x in range(0, self.size_world[0]):
                result = result + abs(np.multiply(x[i_y][i_x], np.log(abs(np.divide(x[i_y][i_x], y[i_y][i_x])))))
        return result