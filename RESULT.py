import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import cv2
import os
import shutil
import argparse
import yaml
import matplotlib.ticker as mticker


class result:

    def __init__(self, path, name_of_simulation, size_world, size_world_real, position_target, my_robot, my_homebase):

        # Get yaml parameter
        parser = argparse.ArgumentParser()
        parser.add_argument('yaml_file')
        args = parser.parse_args()

        with open(args.yaml_file, 'rt') as fh:
            self.yaml_parameters = yaml.safe_load(fh)

        # Initialize
        self.path = path
        self.name_of_simulation = name_of_simulation
        self.size_world = size_world
        self.size_world_real = size_world_real
        self.scaling = size_world[0] / size_world_real[0]
        self.position_target = position_target
        self.my_robot = my_robot
        self.my_homebase = my_homebase
        self.picture_id = 0

        self.size_point = 1 / 150 * np.sqrt(self.size_world_real[0] ** 2 + self.size_world_real[1] ** 2)  # circa 0.943

        # Generate new folder
        os.makedirs(self.path + '/construction', exist_ok=True)


    def build_xy(self, belief_state):
        distance_x = np.linspace(0, self.size_world[0] - 1, self.size_world[0])
        distance_y = np.linspace(0, self.size_world[1] - 1, self.size_world[1])
        x = self.gaussian(distance_x, belief_state[0])
        y = self.gaussian(distance_y, belief_state[1])

        result = [[0 for i in range(self.size_world[0])] for j in range(self.size_world[1])]
        for j in range(self.size_world[1]):
            for i in range(self.size_world[0]):
                result[j][i] = x[i] * y[j]
        return result / np.sum(result)


    def build_rphi(self, position, belief_state):
        result = [[0 for i in range(self.size_world[0])] for j in range(self.size_world[1])]

        for j in range(self.size_world[1]):
            for i in range(self.size_world[0]):
                i_phi = np.arctan2(j - position[1], i - position[0])
                i_r = np.sqrt((i - position[0]) ** 2 + (j - position[1]) ** 2)
                phi = self.gaussian_phi(i_phi, belief_state[0])
                r = self.gaussian(i_r, belief_state[1])
                result[j][i] = r * phi
        return result / np.sum(result)


    def gaussian(self, x, mean_std):
        mean = mean_std[0]
        std = mean_std[1]
        normal_distr = 1 / np.sqrt(2 * np.pi * std ** 2) * np.exp(- np.square(np.subtract(x, mean)) / (2 * std ** 2))
        return normal_distr


    def gaussian_phi(self, x, mean_std):
        mean = mean_std[0]
        std = mean_std[1]
        difference = np.min([abs(x - mean), abs(x - 2 * np.pi - mean), abs(x + 2 * np.pi - mean)])
        normal_distr = 1 / np.sqrt(2 * np.pi * std ** 2) * np.exp(- np.square(difference) / (2 * std ** 2))
        return normal_distr


    def colorbar(self, mappable):
        from mpl_toolkits.axes_grid1 import make_axes_locatable
        import matplotlib.pyplot as plt
        last_axes = plt.gca()
        ax = mappable.axes
        fig = ax.figure
        divider = make_axes_locatable(ax)
        cax = divider.append_axes("right", size="5%", pad=0.05)
        cbar = fig.colorbar(mappable, cax=cax, format='%.0e')
        plt.sca(last_axes)
        return cbar


    def label(self, ax):
        ax.xaxis.set_major_formatter(mticker.FormatStrFormatter('%d m'))
        ax.yaxis.set_major_formatter(mticker.FormatStrFormatter('%d m'))
        for txt in ax.xaxis.get_majorticklabels():
            txt.set_rotation(45)
        for txt in ax.yaxis.get_majorticklabels():
            txt.set_rotation(45)


    def picture_save(self):
        color_robot = 'red'
        color_neighbour = 'white'
        color_target = 'black'

        # Save picture of each step
        fig, (ax) = plt.subplots(len(self.my_robot) + 1, len(self.my_robot) + 1, figsize = (60 / 10 * (len(self.my_robot) + 1), (60 / 10 * (len(self.my_robot) + 1))))
        fig.subplots_adjust(wspace=0.35)
        for x in range(len(self.my_robot)):

            # Actually generating the belief_position
            my_belief_position = [0] * len(self.my_robot)
            for y in range(len(self.my_robot)):
                if y == self.my_robot[x].id_robot:
                    my_belief_position[y] = self.build_xy(self.my_robot[x].my_belief_position.belief_state[y])

                else:
                    # Increase uncertainty because my position where I observe from, is uncertain as well
                    self.my_robot[x].my_belief_position.belief_state[y][0][1] = np.sqrt(self.my_robot[x].my_belief_position.belief_state[y][0][1] ** 2 + (self.my_robot[x].my_belief_position.belief_state[x][0][1] / self.my_robot[x].my_belief_position.belief_state[y][1][0]) ** 2)
                    self.my_robot[x].my_belief_position.belief_state[y][1][1] = np.sqrt(self.my_robot[x].my_belief_position.belief_state[y][1][1] ** 2 + self.my_robot[x].my_belief_position.belief_state[x][0][1] ** 2)

                    my_belief_position[y] = self.build_rphi(self.my_robot[x].position_robot_estimate[x], self.my_robot[x].my_belief_position.belief_state[y])

            # Belief_state_target
            img = ax[x,0].imshow(self.my_robot[x].my_belief_target.belief_state, extent=[0,self.size_world_real[0],self.size_world_real[1],0])
            self.colorbar(img)
            self.label(ax[x, 0])

            # Position estimate of my own position
            pos = patches.Circle(np.divide(self.my_robot[x].position_robot_estimate[x], self.scaling), radius=self.size_point, color=color_robot, fill=True)
            ax[x, 0].add_patch(pos)

                # Rising sign
            if self.my_robot[x].id_contact[-1][0] != 0:
                ris = patches.Circle(np.divide(self.my_robot[x].position_robot_estimate[x], self.scaling), radius=self.size_point * 3, color=color_robot, fill=False)
                ax[x, 0].add_patch(ris)

                # Path of past positions (only make a dot when I take a decision)
            pas = []
            for i in range(int(len(self.my_robot[x].my_belief_target.position_log_estimate[x]) / self.yaml_parameters['deciding_rate'])):
                pas = pas + [patches.Circle(np.divide(self.my_robot[x].my_belief_target.position_log_estimate[x][i * self.yaml_parameters['deciding_rate']], self.scaling), radius=self.size_point / 3, color=color_robot, fill=True)]
                ax[x, 0].add_patch(pas[i])

                # Position of target
            tar = patches.Circle(np.divide(self.position_target, self.scaling), radius=self.size_point, color=color_target, fill=False)
            ax[x, 0].add_patch(tar)

            ax[x, 0].set_title('Belief of robot ' + str(x) + ' about target')

            # Make connecting line when contact between robots
            for y in range(len(self.my_robot[x].position_robot_estimate)):
                contact = self.my_robot[x].id_contact[y][0]
                if (contact == 1) & (x != y):
                    nei_x = (self.my_robot[x].position_robot_estimate[x][0] + self.my_robot[x].my_belief_position.belief_state[y][1][0] * np.cos(self.my_robot[x].my_belief_position.belief_state[y][0][0]))/self.scaling
                    nei_y = (self.my_robot[x].position_robot_estimate[x][1] + self.my_robot[x].my_belief_position.belief_state[y][1][0] * np.sin(self.my_robot[x].my_belief_position.belief_state[y][0][0]))/self.scaling

                    lin = patches.ConnectionPatch(np.divide(self.my_robot[x].position_robot_estimate[x], self.scaling), [nei_x, nei_y], "data", color=color_neighbour)
                    ax[x, 0].add_patch(lin)

                    nei = patches.Circle([nei_x, nei_y], radius=self.size_point, color=color_neighbour, fill=True)
                    ax[x, 0].add_patch(nei)

            # Belief_state_position
            for y in range(len(self.my_robot[x].position_robot_estimate)):
                img = ax[x, y + 1].imshow(my_belief_position[y], extent=[0,self.size_world_real[0],self.size_world_real[1],0])
                self.colorbar(img)
                self.label(ax[x, y + 1])
                nei = patches.Circle((np.divide(self.my_robot[x].position_robot_exact[y], self.scaling)), radius=self.size_point, color=color_neighbour, fill=True)
                ax[x, y + 1].add_patch(nei)

                nei_b = patches.Circle((np.divide(self.my_robot[x].position_robot_exact[y], self.scaling)), radius=self.size_point / 3, color='black', fill=True)
                ax[x, y + 1].add_patch(nei_b)

                pos = patches.Circle((np.divide(self.my_robot[x].position_robot_estimate[x], self.scaling)), radius=self.size_point, color=color_robot, fill=True)
                ax[x, y + 1].add_patch(pos)

                ax[x, y + 1].set_title('Belief of robot ' + str(x) + ' about position of robot ' + str(y))

        # hb_belief_state_target
        img = ax[-1, 0].imshow(self.my_homebase.my_belief_target.belief_state, extent=[0, self.size_world_real[0], self.size_world_real[1], 0])
        self.colorbar(img)
        self.label(ax[-1, 0])

        tar = patches.Circle(np.divide(self.position_target, self.scaling), radius=self.size_point, color=color_target, fill=False)
        ax[-1, 0].add_patch(tar)

        ax[-1, 0].set_title('Belief of home base about target')

        # Actually generating the belief_position
        my_hb_belief_position = [0] * len(self.my_robot)
        for y in range(len(self.my_robot)):
            my_hb_belief_position[y] = self.build_xy(self.my_homebase.my_belief_position.belief_state[y])

        # hb_belief_state_position
        for y in range(len(self.my_robot)):
            img = ax[-1, y + 1].imshow(my_hb_belief_position[y], extent=[0, self.size_world_real[0], self.size_world_real[1], 0])
            self.colorbar(img)
            self.label(ax[-1, y + 1])
            ax[-1, y + 1].set_title('Belief of home base about position of robot ' + str(y))

        plt.savefig(self.path + '/construction/' + str(self.picture_id) + '.png')
        #plt.savefig(self.path + '/construction/' + str(self.picture_id) + '.pdf')
        plt.close()
        self.picture_id = self.picture_id + 1


    def video_save(self):
        # Make video out of all the pictures, previously taken
        img_array = []

        for x in range(0,self.picture_id):
            img = cv2.imread(('./' + self.path + '/construction/' + '{0}.png').format(x))
            height, width, layers = img.shape
            size = (width, height)
            img_array.append(img)

            out = cv2.VideoWriter(self.path + '/video/' + self.name_of_simulation + '.mp4', cv2.VideoWriter_fourcc(*'mp4v'), 20, size)

            for i in range(len(img_array)):
                out.write(img_array[i])
            out.release()

        # Delete folder of pictures
        for i in range(self.picture_id):
            os.remove('./' + self.path + '/construction/' + str(i) + '.png')
        shutil.rmtree(self.path + '/construction')