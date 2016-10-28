import vk
import matplotlib.pyplot as plt
import networkx as NX
import igraph
import pickle
import logging

class LoadData:
	def __init__(self, app=None, login=None, password=None):
		if login is not None and password is not None and app is not None:
			self._session = vk.AuthSession(app_id=app, user_login=login, user_password=password)
		else:
			self._session = vk.Session()
		self._api = vk.API(self._session)
		# print(self._api.users.get(user_ids=62936719))

	def get_all_user_info(self, user_id):
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
	def get_user_friends(self, user_id):
		counter = 0
		while counter < 5:
			try:
				res = self._api.friends.get(user_id=user_id)
				break
			except:
				res = []
				counter += 1


		return res

	def get_user_friends_info(self, user_id):
		friend_ids = self.get_user_friends(user_id)
		friends_info = {}
		for i, x in enumerate(friend_ids):
			if i % 10 == 0:
				print('load {0:d}'.format(i))

			# if i > 20:
			# 	break
			usr_friends = self.get_user_friends(user_id=x)
			friends_info.update({x: self.get_all_user_info(user_id=x)})

		return friends_info

class UserAnalyzer:
	def __init__(self, app=None, login=None, password=None):
		self._source_data = LoadData(app=app, login=login, password=password)
		self._log = logging.getLogger('res')

	def userGraph(self, user_id):
		self._social_graph = NX.Graph()

		self._user_friends_id = self._source_data.get_user_friends(user_id=user_id)
		node_id = {}

		for k, i in enumerate(self._user_friends_id):
			self._social_graph.add_node(k)
			node_id.update({i: k})

		for k, i in enumerate(self._user_friends_id):
			n = self._source_data.get_user_friends(user_id=i)

			for j in n:
				if j in self._user_friends_id:
					# print(node_id[j], k)
					self._social_graph.add_edge(node_id[j], k)

		# print(self._social_graph)
		# NX.drawing.nx_agraph.write_dot(self._social_graph, 'graph.dot')

		# self._friends_info = {x: self._source_data.get_all_user_info(x) for x in user_friends}
		self._friends_info = {}

		for i, x in enumerate(self._user_friends_id):
			if i % 10 == 0:
				self._log.debug('load {0:d}'.format(i))
				# print(i)
			self._friends_info.update({i: self._source_data.get_all_user_info(x)})

		"""for x in self._friends_info.keys():
			print(x, self._friends_info[x])"""
		# NX.draw(self._social_graph, node_size=30, with_labels=True)
		# plt.savefig('graph.png')
		# plt.show()

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

		friends_univers = {}
		univerities = {}

		for i in self._friends_info.keys():
			u = self._friends_info[i].get('university')

			if u:
				# print(self._friends_info[i])
				friends_univers.update({i: self._friends_info[i]})
				univerities.update({u: self._friends_info[i].get('university_name')})

		clusters_number = self.graphClasterization()

		labels = []
		for i in self._clust:
			if len(i) > 10:
				op_proc, data = self._countUniversities(i)

				s = sorted(data, reverse=True, key=lambda x: x[1])
				if len(s) > 0:
					labels.append((s[0][0], s[0][1], s[0][1] * op_proc * len(i)))


				# print(len(i), op_proc, s)


		max_p = max(labels, key=lambda a: a[2])[2]

		# print('max_p', max_p)

		s = []
		for i in labels:
			s.append((i[0], i[1] * i[2] / max_p))

		res = max(s, key=lambda a: a[1])
		print('res', res, univerities[res[0]])
		self._log.info('name: {0:s} max_p: {1:f} university: {2:s}'.format(max_p, univerities[res[0]]))
		# print(list_of_universites)
		# print(len(friends_univers))
		# print(len(list_of_universites))
		"""for i in univerities.keys():
			print(i, univerities[i])"""
	def draw(self):
		NX.draw(self._social_graph, node_size=30, with_labels=False)
		plt.savefig('graph.png')
		# plt.show()

	def graphClasterization(self):
		# print(NX.to_edgelist(self._social_graph))

		# print(list(zip(*list(zip(*NX.to_edgelist(self._social_graph)))[:2])))
		# a = zip(*NX.to_edgelist(self._social_graph))
		g = igraph.Graph(len(self._social_graph), list(zip(*list(zip(*NX.to_edgelist(self._social_graph)))[:2])))

		# print(g)
		# layout = g.layout('kk')
		# igraph.plot(g, layout=layout)
		res = g.community_walktrap()

		clusters = res.as_clustering()
		# print(clusters[0])
		# print(clusters)
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
					# print('yes')
					self._friends_info[j]['cluster'].append(k)
				k = k + 1

		# print(self._user_friends_id)
		# print(self._friends_info.keys())

		# for i in self._user_friends_id:
		# 	print(self._friends_info[i]['cluster'])
		# print(res)

		self._clust = sorted(clusters, reverse=True, key=lambda x: len(x))
		# print(self._clust)

		return len(clusters)
		pass

	def Age(self):
		pass