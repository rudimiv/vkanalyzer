from load_vk_data import UserAnalyzer
from load_vk_data import LoadData
import logging
import argparse
import sys

def main():
	pars = argparse.ArgumentParser()
	pars.add_argument('-i', '--iduser', dest='userid', type=int)
	pars.add_argument('-u', '--university', dest='university', action='store_true')
	pars.add_argument('-a', '--age', dest='age', action='store_true')
	pars.add_argument('-v', '--verbose', dest='v', action='store_true')
	args = pars.parse_args(sys.argv[1:])



	res_log = logging.getLogger('res')

	if not args.v:
		res_log.setLevel(logging.INFO)
	else:
		res_log.setLevel(logging.DEBUG)

	handler = logging.StreamHandler()
	res_log.addHandler(handler)

	res_log.debug('start')

	analyzer = UserAnalyzer()
	analyzer.userGraph(args.userid)

	if args.university:
		analyzer.classifyByUniversity()

	if args.age:
		analyzer.age()



if __name__ == '__main__':
	main()