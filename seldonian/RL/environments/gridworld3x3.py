""" 3x3 gridworld environment (states: 0-8) with a reward function of 0 everywhere
except in r=-1 in cell 7 (bottom middle) and r=1 in cell 8 (bottom right).
Actions are 0,1,2,3 for up,down,left,right respectively. 
An episode starts in cell 0 (top left) and terminates in cell 8
or if timeout occurs. 
"""

import autograd.numpy as np   # Thinly-wrapped version of Numpy
import pickle
import pandas as pd
from functools import lru_cache, partial
from concurrent.futures import ProcessPoolExecutor
import multiprocessing as mp
from tqdm import tqdm

from seldonian.utils.stats_utils import weighted_sum_gamma

class Environment():
	def __init__(self):
		""" 3x3 gridworld environment (states: 0-8) with a 
		reward function of 0 everywhere except 
		r=-1 in cell 7 (bottom middle) and
		r=1 in cell 8 (bottom right). 
		Actions are 0,1,2,3 for up,down,left,right respectively. 
		An episode starts in cell 0 (top left) and terminates in cell 8
		or if timeout occurs. 
		
		:ivar gamma: Discount factor when calculating returns
		:vartype gamma: float

		:ivar timeout: The number of timesteps after which we 
			terminate the agent regardless of state
		:vartype timeout: int

		:ivar states: The possible states 
		:vartype states: numpy ndarray(int)

		:ivar actions: The possible actions
		:vartype actions: numpy ndarray(int)

		:ivar reward_dict: Maps state, action pair to reward
		:vartype reward_dict: dict

		:ivar environ_dict: Maps state, action pair to next state
		:vartype environ_dict: dict

		:ivar initial_state: Where the agent starts each episode
		:vartype initial_state: int

		:ivar terminal_state: The terminal state 
		:vartype terminal_state: int

		:ivar current_state: The current state of the agent
		:vartype current_state: int

		:ivar initial_weights: The initial parameter weights 
			of the agent's policy model
		:vartype initial_weights: numpy ndarray

		:ivar param_weights: The current parameter weights 
			of the agent's policy model
		:vartype param_weights: numpy ndarray		
		"""
		self.gamma = 0.9 # the discount factor when calculating sum of rewards
		self.timeout = 50 # the number of timesteps after which we stop the episode

		self.states = np.arange(9,dtype='int') # 0-8
		self.actions = np.array([0,1,2,3]) # U,D,L,R
		
		self.reward_dict = {x:0 for x in self.states} # initialize
		self.reward_dict[7]=-1
		self.reward_dict[8]=1

		self.environ_dict = {}
		self.environ_dict[0] = {0:0,1:3,2:0,3:1}
		self.environ_dict[1] = {0:1,1:4,2:0,3:2}
		self.environ_dict[2] = {0:2,1:5,2:1,3:2}
		self.environ_dict[3] = {0:0,1:6,2:3,3:4}
		self.environ_dict[4] = {0:1,1:7,2:3,3:5}
		self.environ_dict[5] = {0:2,1:8,2:4,3:5}
		self.environ_dict[6] = {0:3,1:6,2:6,3:7}
		self.environ_dict[7] = {0:4,1:7,2:6,3:8}
		self.environ_dict[8] = {0:5,1:8,2:7,3:8}
		
		self.initial_state = 0
		self.terminal_state = 8

		self.current_state = self.initial_state

		self.initial_weights = np.zeros(
			(len(self.states)-1)*len(self.actions))
		self.param_weights = self.initial_weights

	# @lru_cache
	def _denom(self,state):
		"""Helper function for pi()"""
		return np.sum(np.exp(self.param_weights[state*4+self.actions]))

	# @lru_cache
	def _arg(self,state,action):
		"""Helper function for pi()"""
		return self.param_weights[state*4+action]

	def pi(self,state,action):
		""" Apply the tabular softmax policy
		to get action probability at a given state

		:param state: a position on the gridworld between 0-8
		:type state: int

		:param action: 0,1,2, or 3 corresponding to up,down,left,right
		:type action: int
		"""
		state = int(state)
		action = int(action)
		
		return np.exp(self._arg(state,action))/self._denom(state)

	def take_step(self):
		"""Take an action using the policy and change the state
		"""
		
		step_entry = [0,0,0,0] # s,a,r,pi
			
		step_entry[0] = self.current_state
		
		probs = [self.pi(
			self.current_state,a) for a in self.actions]
		action = np.random.choice(self.actions,p=probs)
		
		step_entry[1] = action

		# Figure out what the actual probability of selecting that action was
		# action_index = self.actions.index(action)
		action_index = np.where(self.actions==action)[0][0]
		
		prob_thisaction = probs[action_index]
			
		# Figure out next state based on this action
		next_state = self.environ_dict[self.current_state][action]
		# Calculate reward for taking that action
		reward = self.reward_dict[next_state]
		# add to episode entry
		step_entry[2] = reward
		
		step_entry[3] = prob_thisaction
			
		# update current state to new state
		self.current_state = next_state
		return step_entry

	def reset(self):
		""" Resets the agent to the initial state. """
		self.current_state = self.initial_state
		return
		

	def generate_episode_flat(self):
		""" Generate an entire episode as a flattened array 
		using the current policy

		:param return_index: Whether to return the timestep 
			as part of the episode
		:type return_index: bool

		"""
		episode = []
		timestep = 0
		while self.current_state != self.terminal_state:
			if timestep == self.timeout:
				break
			
			entry = self.take_step()
			
			episode.extend(entry)
			timestep+=1

		self.reset()
		return episode

	def generate_episodes_flat_par(self,n_episodes):
		""" Generate an entire episode as a flattened array 
		using the current policy

		"""
		np.random.seed()
		episodes = []
		for _ in range(n_episodes):
			episode = []
			timestep = 0
			while self.current_state != self.terminal_state:
				if timestep == self.timeout:
					break
				
				entry = self.take_step()

				episode.extend(entry)
				timestep+=1
			episodes.append(episode)
			self.reset()
		return episodes

	def generate_flat_data(self,n_episodes,parallel=True,
		n_workers=8,savename=None,header=False):
		""" Generate a pandas dataframe where each row is one episode
		like: 
		state_0,action_0,reward_0,probability_of_action_0,state_1,action_1,...
		for n_episodes episodes using the current policy.

		:param n_episodes: The number of episodes to return
		:type n_episodes: int
		
		:param parallel: Whether to use multiple workers 
			to generate the data
		:type parallel: bool

		:param n_workers: The number of workers to use if
			using multiprocessing
		:type n_workers: int

		:param savename: The name of the file in which to 
			save the dataframe  
		:type savename: str, defaults to None

		:param header: Whether to include the column names 
			in the saved dataframe
		:type header: bool, defaults to False
		"""
		if parallel:
			chunk_size = n_episodes//n_workers
			episodes_per_worker = []
			cumulative_episodes = 0
			for i in range(n_workers):
				if i != n_workers - 1:
					episodes_per_worker.append(chunk_size)
					cumulative_episodes+=chunk_size
				else:
					episodes_per_worker.append(n_episodes-cumulative_episodes)
	
			episodes = []
			with ProcessPoolExecutor(max_workers=n_workers,
				mp_context=mp.get_context('fork')) as executor:
				for episode_list in tqdm(executor.map(
					self.generate_episodes_flat_par,
					episodes_per_worker),total=n_workers):
					episodes.extend(episode_list)
		else:
			episodes = [self.generate_episode_flat() for ii in range(n_episodes)]
		
		max_eplen = max([len(x) for x in episodes])
		columns = []
		for ii in range(max_eplen//4):
		    columns.extend([f's_{ii}',f'a_{ii}',f'r_{ii}',f'pi_{ii}'])


		df = pd.DataFrame(list(episodes),columns=columns)
		# df = df.astype({
		# 	"O": int,
		# 	"A": int,
		# 	"R": float,
		# 	"pi": float
		# 	})

		if savename:
			if savename.endswith('.csv'):
				df.to_csv(savename,index=False,header=header)
			elif savename.endswith('.pkl'):
				with open(savename,'wb') as outfile:
					pickle.dump(df,outfile)
			print(f"Saved {savename}")
		return df 


	def generate_episode(self,return_index=False):
		""" Generate an entire episode using the current policy

		:param return_index: Whether to return the timestep 
			as part of the episode
		:type return_index: bool

		"""
		episode = []
		timestep = 0
		while self.current_state != self.terminal_state:
			if timestep == self.timeout:
				break
			
			entry = self.take_step()
			if return_index:
				entry = np.hstack([timestep,entry])
				episode.append([entry])
			else:
				episode.append(entry)
			timestep+=1

		self.reset()
		return episode

	def generate_episodes_par(self,n_episodes=1,return_index=False):
		""" Generate n_episodes episodes using the current policy.
		This is the function to use for multiprocessing   

		:param n_episodes: The number of episodes to return
		:type n_episodes: int
		
		:param return_index: Whether to return the timestep 
			as part of each episode
		:type return_index: bool

		"""
		np.random.seed()
		episodes = []
		for _ in range(n_episodes):
			episode = []
			timestep = 0
			while self.current_state != self.terminal_state:
				if timestep == self.timeout:
					break

				entry = self.take_step()
				if return_index:
					entry = np.hstack([timestep,entry])
					episode.append([entry])
				else:
					episode.append(entry)
				timestep+=1
			episodes.append(episode)
			self.reset()
		return episodes 

	def generate_data(self,n_episodes,parallel=True,
		n_workers=8,savename=None,header=False):
		""" Generate a pandas dataframe consisting of columns:
		episode_index,state,action,reward,probability_of_action
		for n_episodes episodes using the current policy.

		:param n_episodes: The number of episodes to return
		:type n_episodes: int
		
		:param parallel: Whether to use multiple workers 
			to generate the data
		:type parallel: bool

		:param n_workers: The number of workers to use if
			using multiprocessing
		:type n_workers: int

		:param savename: The name of the file in which to 
			save the dataframe  
		:type savename: str, defaults to None

		:param header: Whether to include the column names 
			in the saved dataframe
		:type header: bool, defaults to False
		"""
		if parallel:
			chunk_size = n_episodes//n_workers
			episodes_per_worker = []
			cumulative_episodes = 0
			for i in range(n_workers):
				if i != n_workers - 1:
					episodes_per_worker.append(chunk_size)
					cumulative_episodes+=chunk_size
				else:
					episodes_per_worker.append(n_episodes-cumulative_episodes)

			helper = partial(self.generate_episodes_par,return_index=False)

			with ProcessPoolExecutor(max_workers=n_workers,
				mp_context=mp.get_context('fork')) as executor:
				episodes = tqdm(executor.map(helper, episodes_per_worker),
					total=n_workers)

			data = []
			episode_index = 0
			for list_of_episodes in episodes:
				try:
					for episode in list_of_episodes:
						for entry in episode:
							data.append(np.hstack([episode_index,entry]))
						episode_index+=1
				except Exception as e:
					print(e)
		else:
			episodes = [self.generate_episode(return_index=False) for ii in range(n_episodes)]
			data = []
			for episode_i,episode in enumerate(episodes):
				for step in episode:
					data.append([episode_i]+step)


		# df = pd.DataFrame(data,columns=['episode_index','timestep','O','A','R','pi'])
		# print(data)
		df = pd.DataFrame(data,columns=['episode_index','O','A','R','pi'])
		df = df.astype({
			"episode_index": int, 
			# "timestep": int,
			"O": int,
			"A": int,
			"R": float,
			"pi": float
			})

		if savename:
			if savename.endswith('.csv'):
				df.to_csv(savename,index=False,header=header)
			elif savename.endswith('.pkl'):
				with open(savename,'wb') as outfile:
					pickle.dump(df,outfile)
			print(f"Saved {savename}")
		return df 

	def calc_J(self,param_weights,
		n_episodes,parallel=True,n_workers=8):
		""" Calculate the expected return of the sum 
		of discounted rewards by generating episodes

		:param param_weights: The parameter weights to use
			when generating new episodes
		:type param_weights: numpy ndarray 


		:param n_episodes: The number of episodes to use for 
			calculating the performance
		:type n_episodes: int

		:param parallel: Whether to use multiple workers 
			to generate the data
		:type parallel: bool

		:param n_workers: The number of workers to use if
			using multiprocessing
		:type n_workers: int

		:return: J, the expected return of the sum 
			of discounted rewards
		:rtype: float
		"""
		self.param_weights = param_weights

		df = self.generate_data(
			n_episodes=n_episodes,
			parallel=parallel,
			n_workers=n_workers)

		ws_helper = partial(weighted_sum_gamma,gamma=self.gamma)
		discounted_sum_rewards_episodes=df.groupby(
			'episode_index')['R'].apply(ws_helper)

		return np.mean(discounted_sum_rewards_episodes)
