from colors import colorStr
from console import WIDTH, HEIGHT
from nbinput import NonBlockingInput as nbi


def load_map(filename):
	with open(filename, 'r') as map_file:
		map_ = map_file.readlines()
	return list(zip(*map_))


def move_map(map_, left_edge, right_edge):
	if left_edge < 0 or right_edge > len(map_) - 2:
		return False
	return map_[left_edge : right_edge]


def render_map(map_):
	map_ = list(zip(*map_))
	print('\n'.join(''.join(row) for row in map_))


def main():
	map_ = load_map('map.blks')
	chunk = move_map(map_, 0, 40)
	render_map(chunk)
	chunk = move_map(map_, 2, 42)
	render_map(chunk)

if __name__ == '__main__':
	main()