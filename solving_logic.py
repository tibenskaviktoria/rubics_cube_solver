

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
		print("Error: Unknown color detected in scanned faces")
		return False
	
	expected_colors = {"white", "yellow", "red", "orange", "green", "blue"}
	scanned_colors = set(color_count.keys())
	
	if scanned_colors != expected_colors:
		print(f"Error: Missing or extra colors. Expected {expected_colors}, got {scanned_colors}")
		return False
	
	if all(count == 4 for count in color_count.values()):
		print("Success: All 6 colors scanned correctly with 4 stickers each")
		return True
	else:
		print(f"Error: Color distribution incorrect. Got {color_count}")
		return False
	
