SOLUTION_MIDPOINT = 6 # Optimal solution is at most 11, so the midpoint where bidirectional bfs must go is at most 6

def scanned_faces_correct(captured_faces):
	color_count = {}
	has_unknown = False
	
	for face in captured_faces:
		if face is None:
			continue
		for cell in face:
			label = cell["label"]
			if label == "unknown":
				has_unknown = True
			color_count[label] = color_count.get(label, 0) + 1
	
	if has_unknown:
		return False, "Error: Unknown color detected in scanned faces"
	
	expected_colors = {"white", "yellow", "red", "orange", "green", "blue"}
	scanned_colors = set(color_count.keys())
	
	if scanned_colors != expected_colors:
		return False, f"Error: Missing or extra colors. Expected {expected_colors}, got {scanned_colors}"
	
	if all(count == 4 for count in color_count.values()):
		return True, "Success: All 6 colors scanned correctly with 4 stickers each"
	else:
		return False, f"Error: Color distribution incorrect. Got {color_count}"
	

def generate_scramble_string(captured_faces):
	faces = []
	for face in captured_faces:
		if face is not None:
			face_color_string = "".join(cell["label"][0].upper() for cell in face)
			faces.append(face_color_string)
	return faces


def transform_scan_format_to_solver_input(cube_face_strings):
	"""
	The scanned order of the cube faces is transformed into a format for the solver like so:
	scramble = "ABCDEFGHIJKLMNOPQRSTUVWX"
	- - A B - - - -
	- - C D - - - -
	E F G H I J K L
	M N O P Q R S T
	- - U V - - - -
	- - W X - - - -
	The last scanned face of the cube, which was the bottom face now becomes the GHOP face in the solver input.
	"""
	a = cube_face_strings
	return a[3] + a[2][1] + a[2][3] + a[5][0] + a[5][1] + a[0][2] + a[0][0] + a[4][3] + a[4][2] + a[2][0] + a[2][2] + a[5][2] + a[5][3] + a[0][3] + a[0][1] + a[4][1] + a[4][0] + a[1][3] + a[1][2] + a[1][1] + a[1][0]


def discard_unnecessary_faces(scramble):
	"""
	Removes colors from up, front and right faces as they are not needed to determine the state of cube.
	Because Im only turning the upper, right and front faces to solve the cube, the bottom rear left piece is the only one that will stay exactly where it is so the colors it contains are the only ones I need to keep.
	Therefore from the scramble string I can remove all characters except the ones that represent the colors of the back rear left piece, which are located at indices 12, 19 and 22 in the scramble string.
	"""
	return ''.join([(' ', x)[x in scramble[12]+scramble[19]+scramble[22]] for x in scramble])


def generate_solution(scramble):
	"""
	As explained in the comment of the previous function, the only colors that matter for determining the state of the cube are the ones on the back rear left piece, which are located at indices 12, 19 and 22 in the scramble string.
	Therefore I can generate a solution string by using said colors and putting them in the correct position relative to the solver scramble format.
	"""
	return ' '*4 + scramble[12]*2 + ' '*4 + scramble[19]*2 + scramble[12]*2 + ' '*4 + scramble[19]*2 + scramble[22]*4


permutation = [[0,7,2,15,4,5,6,21,16,8,3,11,12,13,14,23,17,9,1,19,20,18,22,10],  # transformation for R - 0
               [2,0,3,1,6,7,8,9,10,11,4,5,12,13,14,15,16,17,18,19,20,21,22,23],  # transformation for U - 1
               [0,1,13,5,4,20,14,6,2,9,10,11,12,21,15,7,3,17,18,19,16,8,22,23]]  # transformation for F - 2
move_names = "RUF"
turn_names = " 2'"


def applyMove(state, move):
    return ''.join([state[i] for i in permutation[move]])


def get_turn(turn_index, is_reverse):
	if is_reverse:
		res = turn_names[2- turn_index]
	else:
		res = turn_names[turn_index]
	if res == " ":
		return ""
	return res


def bi_directional_BFS(scramble):
	solution = generate_solution(scramble)
	print(f"Generated solution: |{solution}|")
	scramble = discard_unnecessary_faces(scramble)
	print(f"Scramble for BFS:   |{scramble}|")
	
	states_from_scramle = {scramble: ""}
	states_from_solution = {solution: ""}

	for i in range(SOLUTION_MIDPOINT):
		# Search from the side of the initial scramble
		current_states = {}
		for state in states_from_scramle:
			if state in states_from_solution:
				return True, states_from_scramle[state] + " " + states_from_solution[state]
			moves_so_far = states_from_scramle[state]
			new_state = None
			# Apply all the possible moves (9) - R, R2, R', U, U2, U', F, F2, F'
			for move in range(3):
				new_state = state
				# Do each move (R, U, F) 3 times: (eg. U) once - U, twice - U2, thrice - U'
				for turn in range(3):
					new_state = applyMove(new_state, move)
					current_states[new_state] = moves_so_far + " " + move_names[move] + get_turn(turn, False)
		states_from_scramle = current_states
		
		# Search from the side of the solution
		current_states = {}
		for state in states_from_solution:
			if state in states_from_scramle:
				return True, states_from_scramle[state] + " " + states_from_solution[state]
			moves_so_far = states_from_solution[state]
			new_state = None
			# Apply all the possible moves (9) - R, R2, R', U, U2, U', F, F2, F'
			for move in range(3):
				new_state = state
				# Do each move (R, U, F) 3 times: (eg. U) once - U, twice - U2, thrice - U'
				for turn in range(3):
					new_state = applyMove(new_state, move)
					current_states[new_state] = move_names[move] + get_turn(turn, True) + " " + moves_so_far
		states_from_solution = current_states
	return False, "No solution found within depth limit"


def get_cube_solution(captured_faces):
	ret, error_message = scanned_faces_correct(captured_faces)
	if not ret:
		return False, error_message
	face_strings = generate_scramble_string(captured_faces)
	scramble = transform_scan_format_to_solver_input(face_strings)
	print("Transformed scramble for solver input:", scramble)
	return bi_directional_BFS(scramble)
	
