from load_vk_data import UserAnalyzer
from load_vk_data import LoadData
import logging

def main():
	res_log = logging.getLogger('res')
	res_log.setLevel(logging.DEBUG)

	handler = logging.StreamHandler()
	res_log.addHandler(handler)

	res_log.debug('start')


	l = LoadData()
	all_friends = l.get_user_friends(62936719)
	# print(fr)

	for i in all_friends[21:]:
		res_log.info(i)
		try:
			a = UserAnalyzer()
			a.userGraph(i)
			a.classifyByUniversity()
		except:
			res_log.info('error')

	# a.fromFile('graph.b', 'friends.b')

	# a.countClique()
	# a.classifyByUniversity()
	# a.graphClasterization()
	# a.classifyByUniversity()
	# a.draw()

if __name__ == '__main__':
	main()