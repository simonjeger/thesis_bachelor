import numpy as np
import matplotlib.pyplot as plt
import argparse
import yaml


class belief_target_boolean:

    def __init__(self, size_world, my_sensor_target, number_of_robots, id_robot, id_contact):

        # Get yaml parameter
        parser = argparse.ArgumentParser()
        parser.add_argument('yaml_file')
        args = parser.parse_args()

        with open(args.yaml_file, 'rt') as fh:
            self.yaml_parameters = yaml.safe_load(fh)

        # Initialize
        self.size_world = size_world
        self.my_sensor_target = my_sensor_target
        self.number_of_robots = number_of_robots
        self.id_robot = id_robot
        self.id_contact = id_contact

        self.position_log_estimate = [[] for i in range(self.number_of_robots)]
        self.observation_log = [[] for i in range(self.number_of_robots)]
        self.belief_state = [[1 / (self.size_world[0] * self.size_world[1]) for i in range(self.size_world[0])] for j in range(self.size_world[1])]

        self.map_update = [0 for i in range(self.number_of_robots)]


    def update(self, position_next):
        if self.id_contact[-1][0] == 0:
            # Write position in position_log
            self.position_log_estimate[self.id_robot] = self.position_log_estimate[self.id_robot] + [position_next]

            # Sensormeasurement true or false
            measurement = self.my_sensor_target.sense(position_next)
            if measurement != 'no_measurement':
                self.observation_log[self.id_robot] = self.observation_log[self.id_robot] + [measurement]
            else:
                self.observation_log[self.id_robot] = self.observation_log[self.id_robot] + ['no_measurement']
        self.map_construction()


    def map_construction(self):
        for y in range(len(self.position_log_estimate)):
            for x in range(self.map_update[y], len(self.position_log_estimate[y])):
                # Distance to point of measurement
                xw = np.linspace(0, self.size_world[0]-1, self.size_world[0])
                yw = np.linspace(0, self.size_world[1]-1, self.size_world[1])
                xv, yv = np.meshgrid(xw, yw)
                xdiff = xv - self.position_log_estimate[y][x][0]
                ydiff = yv - self.position_log_estimate[y][x][1]
                distance = np.sqrt(xdiff ** 2 + ydiff ** 2)

                if self.observation_log[y][x] != 'no_measurement':
                    likelihood = self.my_sensor_target.likelihood(distance)
                    likelihood = likelihood / np.sum(likelihood)

                else:
                    likelihood = 1 - self.my_sensor_target.likelihood(distance)
                    likelihood = likelihood / np.sum(likelihood)

                # Prior is our current belief
                prior = self.belief_state

                # Posterior (ignore normalization for now)
                posterior = likelihood * prior

                # Update belief
                self.belief_state = posterior

                # Set lower limit for numbers, otherwise numerical errors
                if self.yaml_parameters['lower_bound'] == '':
                    lower_bound, upper_bound = 1e-40, 1
                else:
                    lower_bound, upper_bound = self.yaml_parameters['lower_bound'], 1

                self.belief_state = np.clip(self.belief_state, lower_bound, upper_bound)

                # Now we'll normalize (target must be here somewhere...)
                self.belief_state = self.belief_state / self.belief_state.sum()

                self.map_update[y] = self.map_update[y] + 1


    def merge(self, id_robot, position_log_estimate, observation_log):
        self.position_log_estimate[id_robot] = position_log_estimate
        self.observation_log[id_robot] = observation_log


    def test_true(self, position_observe):
        # Prior is our current belief
        prior = self.belief_state

        # Distance to point of measurement
        xw = np.linspace(0, self.size_world[0]-1, self.size_world[0])
        yw = np.linspace(0, self.size_world[1]-1, self.size_world[1])
        xv, yv = np.meshgrid(xw, yw)
        xdiff = xv - position_observe[0]
        ydiff = yv - position_observe[1]
        distance = np.sqrt(xdiff ** 2 + ydiff ** 2)

        # Sensormeasurement true
        likelihood = self.my_sensor_target.likelihood(distance)

        # Posterior (ignore normalization for now)
        posterior = likelihood * prior

        # Update belief
        test = posterior

        # Now we'll normalize (target must be here somewhere...)
        test = test / np.sum(test)

        return test


    def test_false(self, position_observe):
        # Prior is our current belief
        prior = self.belief_state

        # Distance to point of measurement
        xw = np.linspace(0, self.size_world[0]-1, self.size_world[0])
        yw = np.linspace(0, self.size_world[1]-1, self.size_world[1])
        xv, yv = np.meshgrid(xw, yw)
        xdiff = xv - position_observe[0]
        ydiff = yv - position_observe[1]
        distance = np.sqrt(xdiff ** 2 + ydiff ** 2)

        # Sensormeasurement false
        likelihood = 1 - self.my_sensor_target.likelihood(distance)

        # Posterior (ignore normalization for now)
        posterior = likelihood * prior

        # Update belief
        test = posterior

        # Now we'll normalize (target must be here somewhere...)
        test = test / np.sum(test)

        return test



class belief_target_angle:

    def __init__(self, size_world, my_sensor_target, number_of_robots, id_robot, id_contact):

        # Get yaml parameter
        parser = argparse.ArgumentParser()
        parser.add_argument('yaml_file')
        args = parser.parse_args()

        with open(args.yaml_file, 'rt') as fh:
            self.yaml_parameters = yaml.safe_load(fh)

        # Initialize
        self.size_world = size_world
        self.my_sensor_target = my_sensor_target
        self.number_of_robots = number_of_robots
        self.id_robot = id_robot
        self.id_contact = id_contact

        self.position_log_estimate = [[] for i in range(self.number_of_robots)]
        self.observation_log = [[] for i in range(self.number_of_robots)]
        self.belief_state = [[1 / (self.size_world[0] * self.size_world[1]) for i in range(self.size_world[0])] for j in range(self.size_world[1])]

        self.map_update = [0 for i in range(self.number_of_robots)]


    def update(self, position_next):
        if self.id_contact[-1][0] == 0:
            # Write position in position_log
            self.position_log_estimate[self.id_robot] = self.position_log_estimate[self.id_robot] + [position_next]

            # Sensormeasurement true or false
            measurement = self.my_sensor_target.sense(position_next)
            if measurement != 'no_measurement':
                self.observation_log[self.id_robot] = self.observation_log[self.id_robot] + [measurement]
            else:
                self.observation_log[self.id_robot] = self.observation_log[self.id_robot] + ['no_measurement']
        self.map_construction()


    def map_construction(self):
        for y in range(len(self.position_log_estimate)):
            for x in range(self.map_update[y], len(self.position_log_estimate[y])):
                # Distance to point of measurement
                xw = np.linspace(0, self.size_world[0]-1, self.size_world[0])
                yw = np.linspace(0, self.size_world[1]-1, self.size_world[1])
                xv, yv = np.meshgrid(xw, yw)
                xdiff = xv - self.position_log_estimate[y][x][0]
                ydiff = yv - self.position_log_estimate[y][x][1]
                distance = np.sqrt(xdiff ** 2 + ydiff ** 2)

                if self.observation_log[y][x] != 'no_measurement':
                    measurement = self.observation_log[y][x]

                    xw = np.linspace(0, self.size_world[0]-1, self.size_world[0])
                    yw = np.linspace(0, self.size_world[1]-1, self.size_world[1])
                    xv, yv = np.meshgrid(xw, yw)
                    xdiff = xv - self.position_log_estimate[y][x][0]
                    ydiff = yv - self.position_log_estimate[y][x][1]
                    angle_abs = np.arctan2(ydiff, xdiff)
                    angle = np.minimum(np.minimum(abs(angle_abs - measurement), abs(angle_abs - measurement - 2 * np.pi)), abs(angle_abs - measurement + 2 * np.pi))

                    likelihood_boolean = self.my_sensor_target.likelihood(distance)
                    likelihood_angle = self.my_sensor_target.likelihood_angle(angle)

                    likelihood = likelihood_boolean * likelihood_angle
                    likelihood = likelihood / np.sum(likelihood)

                else:
                    likelihood = 1 - self.my_sensor_target.likelihood(distance)
                    likelihood = likelihood / np.sum(likelihood)

                # Prior is our current belief
                prior = self.belief_state

                # Posterior (ignore normalization for now)
                posterior = likelihood * prior

                # Update belief
                self.belief_state = posterior

                # Set lower limit for numbers, otherwise numerical errors
                if self.yaml_parameters['lower_bound'] == '':
                    lower_bound, upper_bound = 1e-40, 1
                else:
                    lower_bound, upper_bound = self.yaml_parameters['lower_bound'], 1
                self.belief_state = np.clip(self.belief_state, lower_bound, upper_bound)

                # Now we'll normalize (target must be here somewhere...)
                self.belief_state = self.belief_state / self.belief_state.sum()

                self.map_update[y] = self.map_update[y] + 1


    def merge(self, id_robot, position_log_estimate, observation_log):
        self.position_log_estimate[id_robot] = position_log_estimate
        self.observation_log[id_robot] = observation_log


    def test_true(self, position_observe):
        # Prior is our current belief
        prior = self.belief_state

        # Distance to point of measurement
        xw = np.linspace(0, self.size_world[0]-1, self.size_world[0])
        yw = np.linspace(0, self.size_world[1]-1, self.size_world[1])
        xv, yv = np.meshgrid(xw, yw)
        xdiff = xv - position_observe[0]
        ydiff = yv - position_observe[1]
        distance = np.sqrt(xdiff ** 2 + ydiff ** 2)

        # Sensormeasurement true
        likelihood = self.my_sensor_target.likelihood(distance)

        # Posterior (ignore normalization for now)
        posterior = likelihood * prior

        # Update belief
        test = posterior

        # Now we'll normalize (target must be here somewhere...)
        test = test / np.sum(test)

        return test


    def test_false(self, position_observe):
        # Prior is our current belief
        prior = self.belief_state

        # Distance to point of measurement
        xw = np.linspace(0, self.size_world[0]-1, self.size_world[0])
        yw = np.linspace(0, self.size_world[1]-1, self.size_world[1])
        xv, yv = np.meshgrid(xw, yw)
        xdiff = xv - position_observe[0]
        ydiff = yv - position_observe[1]
        distance = np.sqrt(xdiff ** 2 + ydiff ** 2)

        # Sensormeasurement false
        likelihood = 1 - self.my_sensor_target.likelihood(distance)

        # Posterior (ignore normalization for now)
        posterior = likelihood * prior

        # Update belief
        test = posterior

        # Now we'll normalize (target must be here somewhere...)
        test = test / np.sum(test)

        return test



class belief_position:

    def __init__(self, scaling, id_robot, position_robot_exact, position_robot_estimate, my_sensor_distance, my_sensor_motion, number_of_robots):

        # Get yaml parameter
        parser = argparse.ArgumentParser()
        parser.add_argument('yaml_file')
        args = parser.parse_args()

        with open(args.yaml_file, 'rt') as fh:
            self.yaml_parameters = yaml.safe_load(fh)

        # Initialize
        self.scaling = scaling
        self.id_robot = id_robot
        self.my_sensor_distance = my_sensor_distance
        self.my_sensor_motion = my_sensor_motion
        self.position_robot_exact = position_robot_exact
        self.position_robot_estimate = position_robot_estimate
        self.number_of_robots = number_of_robots
        self.belief_state = [0] * self.number_of_robots

        # Parameters for belief_position_me
        self.mean_x = self.position_robot_estimate[self.id_robot][0]
        self.std_x = self.yaml_parameters['std_x'] * self.scaling
        self.mean_y = self.position_robot_estimate[self.id_robot][1]
        self.std_y = self.yaml_parameters['std_y'] * self.scaling

        self.belief_state[self.id_robot] = [[self.mean_x, self.std_x], [self.mean_y, self.std_y]]


    def initialize_neighbour(self, id_robot, belief_state):
        dx = belief_state[0][0] - self.position_robot_estimate[self.id_robot][0]
        dy = belief_state[1][0] - self.position_robot_estimate[self.id_robot][1]
        mean_phi = np.arctan2(dy, dx)
        mean_r = np.sqrt(dx ** 2 + dy ** 2)
        std_phi = belief_state[0][1] / mean_r
        std_r = belief_state[0][1]

        self.belief_state[id_robot] = [[mean_phi, std_phi], [mean_r, std_r]]


    def update_robot(self, angle_step_distance):
        self.measurement_angle_step_distance = self.my_sensor_motion.sense(angle_step_distance)

        prior_x = self.belief_state[self.id_robot][0]
        prior_y = self.belief_state[self.id_robot][1]

        likelihood_x = self.my_sensor_motion.likelihood_x(self.measurement_angle_step_distance)
        likelihood_y = self.my_sensor_motion.likelihood_y(self.measurement_angle_step_distance)

        posterior_x = [prior_x[0] + likelihood_x[0], np.sqrt(prior_x[1] ** 2 + likelihood_x[1] ** 2)]
        posterior_y = [prior_y[0] + likelihood_y[0], np.sqrt(prior_y[1] ** 2 + likelihood_y[1] ** 2)]

        self.belief_state[self.id_robot][0] = posterior_x
        self.belief_state[self.id_robot][1] = posterior_y


    def update_neighbour(self):
        for x in range(self.number_of_robots):
            if x != self.id_robot:

                # Transform into coordinate system with new orgin
                self.transform(x)

                # Make measurement (needed for the following process)
                measurement = self.my_sensor_distance.sense(x)
                if measurement != 'no_measurement':
                    likelihood_r = self.my_sensor_distance.likelihood(measurement)

                # Make uncertanty grow because the neighbour moves
                prior_phi = self.belief_state[x][0]
                prior_r = self.belief_state[x][1]

                if measurement != 'no_measurement':
                    velocity_vector_phi = [prior_phi[0], self.my_sensor_motion.std_move / measurement]
                else:
                    velocity_vector_phi = [prior_phi[0], self.my_sensor_motion.std_move / prior_r[0]]

                velocity_vector_r = [prior_r[0], self.my_sensor_motion.std_move]

                new_prior_phi = [prior_phi[0], np.sqrt(prior_phi[1] ** 2 + velocity_vector_phi[1] ** 2)]
                new_prior_r = [prior_r[0], np.sqrt(prior_r[1] ** 2 + velocity_vector_r[1] ** 2)]

                # Make measurement update
                if measurement != 'no_measurement':
                    new_mean_r = (new_prior_r[0] * likelihood_r[1] ** 2 + likelihood_r[0] * new_prior_r[1] ** 2) / (new_prior_r[1] ** 2 + likelihood_r[1] ** 2)
                    new_std_r = np.sqrt((new_prior_r[1] ** 2 * likelihood_r[1] ** 2) / (new_prior_r[1] ** 2 + likelihood_r[1] ** 2))
                else:
                    new_mean_r = new_prior_r[0]
                    new_std_r = new_prior_r[1]

                posterior_phi = new_prior_phi
                posterior_r = [new_mean_r, new_std_r]

                self.belief_state[x][0] = posterior_phi
                self.belief_state[x][1] = posterior_r


    def surface(self):
        self.belief_state[self.id_robot] = [[self.position_robot_exact[self.id_robot][0], self.std_x], [self.position_robot_exact[self.id_robot][1], self.std_y]]


    def transform(self, id_robot):
        dx_before = self.belief_state[id_robot][1][0] * np.cos(self.belief_state[id_robot][0][0])
        dy_before = self.belief_state[id_robot][1][0] * np.sin(self.belief_state[id_robot][0][0])
        dx_trans = self.measurement_angle_step_distance[1] * np.cos(self.measurement_angle_step_distance[0])
        dy_trans = self.measurement_angle_step_distance[1] * np.sin(self.measurement_angle_step_distance[0])

        dx_now = dx_before - dx_trans
        dy_now = dy_before - dy_trans

        # Unnormalize the std (makes it independent of old mean_r)
        std_phi = self.belief_state[id_robot][0][1] * self.belief_state[id_robot][1][0]

        mean_phi = np.arctan2(dy_now, dx_now)
        mean_r = np.sqrt(dx_now ** 2 + dy_now ** 2)

        # Normalize the std (makes it dependent of new mean_r)
        std_phi = std_phi / mean_r
        std_r = self.belief_state[id_robot][1][1]

        self.belief_state[id_robot] = [[mean_phi, std_phi],[mean_r, std_r]]




class hb_belief_target_boolean:

    def __init__(self, size_world, my_sensor_target, number_of_robots):

        # Initialize
        self.size_world = size_world
        self.my_sensor_target = my_sensor_target
        self.number_of_robots = number_of_robots

        self.position_log_estimate = [[] for i in range(self.number_of_robots)]
        self.observation_log = [[] for i in range(self.number_of_robots)]
        self.belief_state = [[1 / (self.size_world[0] * self.size_world[1]) for i in range(self.size_world[0])] for j in range(self.size_world[1])]

        self.map_update = [0 for i in range(self.number_of_robots)]


    def map_construction(self):
        for y in range(len(self.position_log_estimate)):
            for x in range(self.map_update[y], len(self.position_log_estimate[y])):
                # Distance to point of measurement
                xw = np.linspace(0, self.size_world[0]-1, self.size_world[0])
                yw = np.linspace(0, self.size_world[1]-1, self.size_world[1])
                xv, yv = np.meshgrid(xw, yw)
                xdiff = xv - self.position_log_estimate[y][x][0]
                ydiff = yv - self.position_log_estimate[y][x][1]
                distance = np.sqrt(xdiff ** 2 + ydiff ** 2)

                if self.observation_log[y][x] != 'no_measurement':
                    likelihood = self.my_sensor_target.likelihood(distance)
                    likelihood = likelihood / np.sum(likelihood)

                else:
                    likelihood = 1 - self.my_sensor_target.likelihood(distance)
                    likelihood = likelihood / np.sum(likelihood)

                # Prior is our current belief
                prior = self.belief_state

                # Posterior (ignore normalization for now)
                posterior = likelihood * prior

                # Update belief
                self.belief_state = posterior

                # Now we'll normalize (target must be here somewhere...)
                self.belief_state = self.belief_state / self.belief_state.sum()

                self.map_update[y] = self.map_update[y] + 1


    def merge(self, id_robot, position_log_estimate, observation_log):
        self.position_log_estimate[id_robot] = position_log_estimate
        self.observation_log[id_robot] = observation_log
        self.map_construction()



class hb_belief_target_angle:

    def __init__(self, size_world, my_sensor_target, number_of_robots):

        # Initialize
        self.size_world = size_world
        self.my_sensor_target = my_sensor_target
        self.number_of_robots = number_of_robots

        self.position_log_estimate = [[] for i in range(self.number_of_robots)]
        self.observation_log = [[] for i in range(self.number_of_robots)]
        self.belief_state = [[1 / (self.size_world[0] * self.size_world[1]) for i in range(self.size_world[0])] for j in range(self.size_world[1])]

        self.map_update = [0 for i in range(self.number_of_robots)]

    def map_construction(self):
        for y in range(len(self.position_log_estimate)):
            for x in range(self.map_update[y], len(self.position_log_estimate[y])):
                # Distance to point of measurement
                xw = np.linspace(0, self.size_world[0]-1, self.size_world[0])
                yw = np.linspace(0, self.size_world[1]-1, self.size_world[1])
                xv, yv = np.meshgrid(xw, yw)
                xdiff = xv - self.position_log_estimate[y][x][0]
                ydiff = yv - self.position_log_estimate[y][x][1]
                distance = np.sqrt(xdiff ** 2 + ydiff ** 2)

                if self.observation_log[y][x] != 'no_measurement':
                    measurement = self.observation_log[y][x]

                    xw = np.linspace(0, self.size_world[0]-1, self.size_world[0])
                    yw = np.linspace(0, self.size_world[1]-1, self.size_world[1])
                    xv, yv = np.meshgrid(xw, yw)
                    xdiff = xv - self.position_log_estimate[y][x][0]
                    ydiff = yv - self.position_log_estimate[y][x][1]
                    angle_abs = np.arctan2(ydiff, xdiff)
                    angle = np.min([abs(angle_abs - measurement), abs(angle_abs - measurement - 2 * np.pi), abs(angle_abs - measurement + 2 * np.pi)])

                    likelihood_boolean = self.my_sensor_target.likelihood(distance)

                    likelihood_angle = self.my_sensor_target.likelihood_angle(angle)

                    likelihood = likelihood_boolean * likelihood_angle
                    likelihood = likelihood / np.sum(likelihood)

                else:
                    likelihood = 1 - self.my_sensor_target.likelihood(distance)
                    likelihood = likelihood / np.sum(likelihood)

                # Prior is our current belief
                prior = self.belief_state

                # Posterior (ignore normalization for now)
                posterior = likelihood * prior

                # Update belief
                self.belief_state = posterior

                # Now we'll normalize (target must be here somewhere...)
                self.belief_state = self.belief_state / self.belief_state.sum()

                self.map_update[y] = self.map_update[y] + 1


    def merge(self, id_robot, position_log_estimate, observation_log):
        self.position_log_estimate[id_robot] = position_log_estimate
        self.observation_log[id_robot] = observation_log
        self.map_construction()



class hb_belief_position:

    def __init__(self, my_sensor_motion, position_robot_exact, number_of_robots):

        # Initialize
        self.my_sensor_motion = my_sensor_motion
        self.position_robot_exact = position_robot_exact
        self.number_of_robots = number_of_robots
        self.belief_state = [0] * self.number_of_robots

        # Parameters for belief_position
        self.std_x = 1
        self.std_y = 1

        for i in range(self.number_of_robots):
            self.belief_state[i] = [[self.position_robot_exact[i][0], self.std_x], [self.position_robot_exact[i][1], self.std_y]]

    def update(self):
        for x in range(self.number_of_robots):

            # Make uncertanty grow because the neighbour moves
            prior_x = self.belief_state[x][0]
            prior_y = self.belief_state[x][1]

            velocity_vector_x = [prior_x[0], self.my_sensor_motion.std_move]
            velocity_vector_y = [prior_y[0], self.my_sensor_motion.std_move]

            new_prior_x = [prior_x[0], np.sqrt(prior_x[1] ** 2 + velocity_vector_x[1] ** 2)]

            new_prior_y = [prior_y[0], np.sqrt(prior_y[1] ** 2 + velocity_vector_y[1] ** 2)]

            self.belief_state[x][0] = new_prior_x
            self.belief_state[x][1] = new_prior_y
