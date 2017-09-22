# hyperpameter optimisation on cart pole framework

from gaussianProcess import gaussian_process, vector_2d, range_handling
from surrogateFunction import next_parameter_by_ei
from writeFunction import write_function
from rlBrain import policy_gradient

import matplotlib.pyplot as plt
import numpy as np
import gym
import random
import math
import sys
import csv

# renders environment if total episode reward is greater then this threshold
DISPLAY_REWARD_THRESHOLD = 400
RENDER = False  # rendering wastes time

env = gym.make('CartPole-v0')
env.seed(1)     # reproducible, general Policy gradient has high variance
env = env.unwrapped

# iteration variables

meta_trials = 10  # 3rd level iterable
optimisation_range = 10  # 2nd level iterable
reinforcement_learning_range = 100 # 1st level iterable
trial_number, learning_rate_array, final_score = [], [], []

for meta_iteration in range(meta_trials):  # third level iteration
	trial_number.append(meta_iteration)

	# hyperparameters
	# optimal learning_rate = 0.02
	learning_rate_range = [0.001, 0.1]
	reward_decay = 0.99
	scores, parameters = [], []
	normalisation_factor, min_learning_rate, max_learning_rate, learning_rate_choices = range_handling(
		learning_rate_range
	)

	for opt_iteration in range(1, optimisation_range + 1):  # second level iteration

		print("This is bayesian iteration: " + str(opt_iteration))
		if opt_iteration in (1, 2):
			learning_rate = random.randint(
				min_learning_rate, max_learning_rate)
			learning_rate = learning_rate * normalisation_factor

		# define RL object
		RL = policy_gradient(
			n_actions=env.action_space.n,
			n_features=env.observation_space.shape[0],
			learning_rate=learning_rate,
			reward_decay=0.99,
			# output_graph=True,
		)

		for i_episode in range(reinforcement_learning_range):  # first level iteration

			observation = env.reset()

			while True:
				#if RENDER:
				#env.render()	

				action = RL.choose_action(observation)
				observation_, reward, done, info = env.step(action)
				RL.store_transition(observation, action, reward)
				 
				if done or sum(RL.ep_rs) > 600:
					ep_rs_sum = sum(RL.ep_rs)

					if 'running_reward' not in globals():
						running_reward = ep_rs_sum
					else:
						running_reward = running_reward * 0.99 + ep_rs_sum * 0.01
					if running_reward > DISPLAY_REWARD_THRESHOLD:
						RENDER = True     # rendering
					print("episode:", i_episode,
						  "  reward:", int(running_reward))

					vt = RL.learn()

					bayesian_cost_value = running_reward  # generate reward value for bayesian
					break

				observation = observation_

		scores.append(bayesian_cost_value)
		parameters.append(learning_rate)

		print scores
		print parameters

		if opt_iteration < 2:
			continue  # 2 samples needed for inference

		y_mean, y_std = gaussian_process(
			parameters, scores, learning_rate_choices)

		y_min = min(scores)

		learning_rate = next_parameter_by_ei(
			y_min, y_mean, y_std, learning_rate_choices)

		if y_min == 0 or learning_rate in parameters:
			break  # lowest expectation achieved

	max_score_index = np.argmax(scores)
	final_score.append(scores[max_score_index])
	learning_rate_array.append(parameters[max_score_index])

	print parameters[max_score_index]  # final learning rate

optimal_learning_rate = max(set(parameters), key=parameters.count)
print "Optimal learning rate : " + str(optimal_learning_rate)

write_function(trial_number, learning_rate_array, final_score)