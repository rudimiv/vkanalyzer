# -*- coding: utf-8 -*-

import vk
import matplotlib.pyplot as plt
import networkx as NX
import igraph
import pickle
import logging
import numpy as np
from threading import Thread

class LoadData:
	def __init__(self, app=None, login=None, password=None):
		self._log = logging.getLogger('res')
		if login is not None and password is not None and app is not None:
			self._session = vk.AuthSession(app_id=app, user_login=login, user_password=password)
		else:
			self._session = vk.Session()
		self._api = vk.API(self._session)
		# print(self._api.users.get(user_ids=62936719))


	def get_all_user_info(self, user_id):
		'''
		Получает информацию о пользователе по его id

		:param user_id: id пользователся
		:type integer
		:return: информация о пользователе
		:rtype dict
		'''
		counter = 0
		while counter < 5:
			try:
				res = self._api.users.get(user_id=user_id, fields=['photo_id', 'verified', 'sex', 'bdate', 'city', 'country',
																   'home_town', 'education'])[0]

				break
			except:
				res = {}
				counter += 1

		res.update({'id': user_id})
		return res

	def get_all_users_info(self, users_id):
		for i in users_id:
			friends_info.update({x: self.get_all_user_info(user_id=x)})

	def get_user_friends(self, user_id):
		'''
		Возвращает список друзей пользователя по его id

		:param user_id: id пользователя
		:type integer
		:return: список друзей
		:rtype list
		'''
		counter = 0
		while counter < 5:
			try:
				res = self._api.friends.get(user_id=user_id)
				break
			except:
				res = []
				counter += 1


		return res

	def get_user_friends_info(self, user_id, number_of_threads=12):
		print('here')
		'''
		Возващает информацию обо всех друзьях пользователя

		:param user_id: id пользователя
		:type integer
		:return: словарь с информацией о друзьях
		:rtype dict
		'''
		friend_ids = self.get_user_friends(user_id)
		friends_info = {}
		"""for i, x in enumerate(friend_ids):
			if i % 10 == 0:
				print('load {0:d}'.format(i))

			friends_info.update()"""

		# разбиение между процессами
		ids_to_process = len(friend_ids) // number_of_threads + 1
		friend_ids_to_processes = [friend_ids[i: i + ids_to_process] for i in range(0, len(friend_ids), ids_to_process)]

		threads = []

		for k, i in enumerate(friend_ids_to_processes):
			self._log.debug('Start {0:d} Thread'.format(k))
			thread = Thread(target=get_all_users_info, args=(i,))
			thread.start()
			threads.append(thread)

		# ждать окончания потока
		for thread in threads:
			thread.join()

		self._log.debug('All threads are terminated')
		return friends_info

class UserAnalyzer:
	def __init__(self, app=None, login=None, password=None):
		self._source_data = LoadData(app=app, login=login, password=password)
		self._log = logging.getLogger('res')

	def userGraph(self, user_id, number_of_threads=12):
		'''
		Построение социального графа пользователя

		:param user_id: id пользователя
		:type integer
		'''

		self._log.debug('creating user {0:d} graph'.format(user_id))
		self._social_graph = NX.Graph()

		self._user_friends_id = self._source_data.get_user_friends(user_id=user_id)

		data = self._source_data.get_all_user_info(user_id=user_id)

		self._user_first_name = data['first_name']
		self._user_last_name = data['last_name']

		self._log.info('{0:s} {1:s}'.format(self._user_first_name, self._user_last_name))
		if not len(self._user_friends_id):
			raise ValueError

		self._node_id = {}

		for k, i in enumerate(self._user_friends_id):
			self._social_graph.add_node(k)
			self._node_id.update({i: k})

		# разбиение между процессами
		ids_to_process = len(self._user_friends_id) // number_of_threads + 1
		friend_ids_to_processes = [self._user_friends_id[i: i + ids_to_process] for i in range(0, len(self._user_friends_id), ids_to_process)]

		threads = []

		for k, i in enumerate(friend_ids_to_processes):
			self._log.debug('Start {0:d} Thread'.format(k))
			thread = Thread(target=self._add_friends_to_social_graph, args=(i, k * ids_to_process))
			thread.start()
			threads.append(thread)

		# ждаем окончания потоков
		for thread in threads:
			thread.join()

		self._log.debug('All threads are terminated')


		self._friends_info = {}

		threads = []

		for k, i in enumerate(friend_ids_to_processes):
			self._log.debug('Start {0:d} Thread'.format(k))
			thread = Thread(target=self._get_friends_info, args=(i, k * ids_to_process))
			thread.start()
			threads.append(thread)

		# ждаем окончания потоков
		for thread in threads:
			thread.join()

		self._log.debug('All threads are terminated')

	def _get_friends_info(self, friends_ids, nodes_num):
		for k, i in enumerate(friends_ids):
			self._friends_info.update({nodes_num + k: self._source_data.get_all_user_info(i)})

	def _add_friends_to_social_graph(self, user_ids, nodes_num):
		for k, i in enumerate(user_ids):
			n = self._source_data.get_user_friends(user_id=i)

			for j in n:
				if j in self._user_friends_id:
					# print(node_id[j], k)
					self._social_graph.add_edge(self._node_id[j], nodes_num + k)


	def fromFile(self, graph_file, friends_file):
		with open(graph_file, 'rb') as g:
			self._social_graph = pickle.load(g)

		with open(friends_file, 'rb') as f:
			self._friends_info = pickle.load(f)

	def toFile(self, graph_file, friends_file):
		with open(graph_file, 'wb') as g:
			pickle.dump(self._social_graph, g)

		with open(friends_file, 'wb') as f:
			pickle.dump(self._friends_info, f)


	def _countUniversities(self, p):
		'''
		Анализирует ВУЗ подгруппы людей

		:param p: список id людей
		:type list
		:return: доля людей с открытой информацией о ВУЗе, список кортежей ВУЗ, процент людей
		:rtype float, [(integer, float)]
		'''
		universities = {}
		counter = 0
		for i in p:
			u = self._friends_info[i].get('university')

			if u:
				if universities.get(u):
					universities[u] = universities[u] + 1
				else:
					universities[u] = 1

				counter = counter + 1

		return counter / len(p), [(i, universities[i] / counter) for i in universities.keys()]

	def classifyByUniversity(self):
		'''
		Производит классификацию пользователя по ВУЗу

		:return:
		'''
		self._log.debug('classify by university')
		friends_univers = {}
		univerities = {}

		for i in self._friends_info.keys():
			u = self._friends_info[i].get('university')

			if u:
				friends_univers.update({i: self._friends_info[i]})
				univerities.update({u: self._friends_info[i].get('university_name')})

		self.graphClasterization()

		labels = []
		for i in self._clust:
			if len(i) > 10:
				op_proc, data = self._countUniversities(i)

				s = sorted(data, reverse=True, key=lambda x: x[1])
				if len(s) > 0:
					labels.append((s[0][0], s[0][1], s[0][1] * op_proc * len(i)))


		max_p = max(labels, key=lambda a: a[2])[2]

		s = []
		for i in labels:
			s.append((i[0], i[1] * i[2] / max_p))

		res_arr = sorted(s, reverse=True, key=lambda a: a[1])
		prev_univers = set()

		for i, res in enumerate(res_arr):
			if res[1] < 0.5:
				break

			if res[0] in prev_univers:
				continue

			self._log.info('ВУЗ: {university:s} коэффициент: {probability:f}'.format(probability=res[1],
																						university=univerities[res[0]]))


			prev_univers.update({res[0]})
			if i > 3:
				break


	def draw(self):
		NX.draw(self._social_graph, node_size=30, with_labels=False)
		plt.savefig('graph.png')
		# plt.show()

	def graphClasterization(self):
		self._log.debug('clusterizing	 graph')

		g = igraph.Graph(len(self._social_graph), list(zip(*list(zip(*NX.to_edgelist(self._social_graph)))[:2])))

		# print(g)
		# layout = g.layout('kk')
		# igraph.plot(g, layout=layout)
		res = g.community_walktrap()

		clusters = res.as_clustering()
		n_color = []
		k = 0
		for i in g.vs:
			if k in clusters[3]:
				n_color.append('red')
			else:
				n_color.append('green')
			k = k + 1
		g.vs['color'] = n_color

		# lay = g.layout('kk')
		# igraph.plot(g, layout=lay)

		k = 0
		for i in clusters:
			for j in i:
				if 'cluster' not in self._friends_info[j].keys():
					self._friends_info[j].update({'cluster': [k]})
				else:
					self._friends_info[j]['cluster'].append(k)
				k = k + 1

		self._clust = sorted(clusters, reverse=True, key=lambda x: len(x))

		return len(clusters)
		pass


	def _countAge(self, p):
		'''
		Анализирует возрастную струкутру

		:param p: список id людей
		:type list
		:return: доля людей с открытой информацикй о возрасте, среднее, дисперсия
		:rtype float, float, float
		'''
		ages = []

		for i in p:
			u = self._friends_info[i].get('bdate')

			if u and len(u.split('.')) == 3:
				ages.append(2016 - int(u.split('.')[2]))


		# отфильтровываем по выбросам
		arr = np.array(ages)
		self._log.debug(arr)

		new_arr = np.empty(0, dtype=int)

		while not np.array_equal(arr, new_arr) and len(arr):
			new_arr = np.empty(0, dtype=int)
			for k, i in enumerate(arr):
				arr_without_elem = np.delete(arr, k)
				aver = np.average(arr_without_elem)
				variance = np.var(arr_without_elem)

				if (abs(i - aver) < 3 * variance):
					new_arr = np.append(new_arr, i)

			arr = np.array(new_arr)


		if not len(arr):
			return None

		if abs(np.var(new_arr)) < 0.000001:
			return (len(arr), len(arr) / len(p), np.average(new_arr), 0.1)
		return (len(arr), len(arr) / len(p), np.average(new_arr), np.var(new_arr))


	def age(self):
		'''
		Классификация людей по возрастам
		:return:
		'''
		self.graphClasterization()

		stat_by_clusters = []

		for i in self._clust:
			if len(i) > 10:
				stat_by_clusters.append(self._countAge(i))

				self._log.debug('new cluster')

		stat_by_clusters = list(filter(lambda a: True if a else False, stat_by_clusters))

		self._log.debug(list(stat_by_clusters))

		max_p = max(stat_by_clusters, key=lambda a: a[0])[0]
		self._log.debug(max_p)

		res = max(stat_by_clusters, key=lambda a: a[0] / max_p * a[1] / a[3])

		self._log.info('Возраст: {age:f} коэффициент: {probability:f}'.format(age=res[2], probability=res[1]))