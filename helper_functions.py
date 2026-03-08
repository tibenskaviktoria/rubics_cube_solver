import cv2
import numpy as np

FACE_COUNT = 6


def get_fixed_cube_guide(frame_shape, guide_ratio=0.38):
	"""Calculates a centered square guide box on the video frame for cube face alignment during scanning."""
	h, w = frame_shape[:2]
	side = int(min(w, h) * guide_ratio)
	cx, cy = w // 2, h // 2
	x1 = cx - side // 2
	y1 = cy - side // 2
	x2 = cx + side // 2
	y2 = cy + side // 2
	return x1, y1, x2, y2


def get_cell_boxes(guide_box):
	"""Given the coordinates of the guide box, calculates the bounding boxes for each of the 4 cells in the 2x2 grid. Returns a list of cell boxes in the format (x1, y1, x2, y2)."""
	x1, y1, x2, y2 = guide_box
	mx = (x1 + x2) // 2
	my = (y1 + y2) // 2

	return [
		(x1, y1, mx, my),
		(mx, y1, x2, my),
		(x1, my, mx, y2),
		(mx, my, x2, y2),
	]


def draw_fixed_2x2_guide(frame, guide_box):
	"""Draws a fixed 2x2 grid guide on the video frame to assist in aligning a face of the cube for scanning."""
	x1, y1, x2, y2 = guide_box

	cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)

	mx = (x1 + x2) // 2
	my = (y1 + y2) // 2
	cv2.line(frame, (mx, y1), (mx, y2), (255, 255, 0), 2)
	cv2.line(frame, (x1, my), (x2, my), (255, 255, 0), 2)


def print_console_instructions():
	print("###                       Instructions                       ###")
	print("###                      ==============                      ###")
	print("###  Begin scanning the cube by pressing \"s\", if you mess    ###")
	print("###  up while scanning just press \"s\" again to restart.      ###")
	print("###  While scanning press SPACE to save the face of the      ###")
	print("###  cube and turn the cube left so that the face on right   ###")
	print("###  of the scanned one is facing the camera. Repeat until   ###")
	print("###  all 4 horizontal faces are scanned and while the last   ###")
	print("###  scanned face is still facing the camera, turn the cube  ###")
	print("###  so that the top face can be scanned, then return to the ###")
	print("###  previous face and turn the cube to the last, bottom     ###")
	print("###  face. Now the whole cube is scanned and solution can    ###")
	print("###  be shown.                                               ###")
	print("################################################################\n")
	

def get_next_scan_hint(captured_count):
	if captured_count == 0:
		return "Press S to start scan. Align first horizontal face, then press SPACE."
	if 1 <= captured_count <= 3:
		return "Turn cube CLOCKWISE. Press SPACE for next face."
	if captured_count == 4:
		return "Now scan TOP face (while face 4 orientation is known), then press SPACE."
	if captured_count == 5:
		return "Return to previous face and rotate cube to scan BOTTOM face. Press SPACE."
	return "All 6 faces scanned. Press S to restart or Q to quit."


def draw_instructions(frame, captured_count):
	text = f"S: start/restart scan | SPACE: save face | Q: quit | Captured: {captured_count}/{FACE_COUNT}"
	cv2.putText(
		frame,
		text,
		(20, frame.shape[0] - 20),
		cv2.FONT_HERSHEY_SIMPLEX,
		0.68,
		(255, 255, 255),
		2,
		cv2.LINE_AA,
	)
	cv2.putText(
		frame,
		"Align one cube face inside this guide",
		(20, 35),
		cv2.FONT_HERSHEY_SIMPLEX,
		0.75,
		(0, 255, 0),
		2,
		cv2.LINE_AA,
	)


def draw_hint(frame, captured_count, status_text, status_color):
	hint_text = get_next_scan_hint(captured_count)
	cv2.putText(
		frame,
		hint_text,
		(20, 95),
		cv2.FONT_HERSHEY_SIMPLEX,
		0.58,
		(255, 255, 255),
		2,
		cv2.LINE_AA,
	)
	cv2.putText(
		frame,
		status_text,
		(20, 65),
		cv2.FONT_HERSHEY_SIMPLEX,
		0.7,
		status_color,
		2,
		cv2.LINE_AA,
	)


def format_face_rows(face_sample):
	"""Formats the labels of a scanned face into two rows for display."""
	labels = [cell["label"] for cell in face_sample]
	return [f"{labels[0][0].upper()} {labels[1][0].upper()}", f"{labels[2][0].upper()} {labels[3][0].upper()}"]


def print_scanned_faces_summary(captured_faces):
	if len(captured_faces) >= FACE_COUNT:
		f1, f2, f3, f4, f5, f6 = [format_face_rows(face) for face in captured_faces[:FACE_COUNT]]

		print("\nScanned faces in 2D representation:")
		print(f"{'':15}{f5[0]}")
		print(f"{'':15}{f5[1]}")
		print(f"{f1[0]}  {f2[0]}  {f3[0]}  {f4[0]}")
		print(f"{f1[1]}  {f2[1]}  {f3[1]}  {f4[1]}")
		print(f"{'':15}{f6[0]}")
		print(f"{'':15}{f6[1]}")

	print("=== End Capture ===\n")
	

def sample_cell_bgr(frame, cell_box):
	"""Samples the average BGR color from a specified cell box area in the video frame, 
	applying padding to avoid edge artifacts. Returns the average color as a tuple (B, G, R)."""
	x1, y1, x2, y2 = cell_box
	pad_x = max(2, (x2 - x1) // 6)
	pad_y = max(2, (y2 - y1) // 6)

	rx1 = x1 + pad_x
	ry1 = y1 + pad_y
	rx2 = x2 - pad_x
	ry2 = y2 - pad_y

	patch = frame[ry1:ry2, rx1:rx2]
	if patch.size == 0:
		return (0, 0, 0)

	b, g, r, _ = cv2.mean(patch)
	return int(b), int(g), int(r)


def classify_bgr_color(bgr: tuple[int, int, int]):
	"""Classifies a given BGR color tuple into one of the cube face colors 
	(white, yellow, red, orange, green, blue) based on HSV thresholds."""
	b, g, r = bgr
	pixel = np.array([[[b, g, r]]], dtype=np.uint8)
	h, s, v = cv2.cvtColor(pixel, cv2.COLOR_BGR2HSV)[0][0]

	if v < 40:
		return "unknown"
	if s < 55 and v > 150:
		return "white"
	if h < 8 or h >= 170:
		return "red"
	if 8 <= h < 22:
		return "orange"
	if 22 <= h < 40:
		return "yellow"
	if 40 <= h < 90:
		return "green"
	if 90 <= h < 140:
		return "blue"

	return "unknown"


def draw_cell_color_markers(frame, cell_boxes, cell_samples):
	"""Draws colored circles and labels on the video frame for each cell in the cube face guide."""
	label_to_bgr = {
		"white": (230, 230, 230),
		"yellow": (0, 255, 255),
		"red": (0, 0, 255),
		"orange": (0, 140, 255),
		"green": (0, 255, 0),
		"blue": (255, 0, 0),
		"unknown": (0, 0, 0),
	}

	for cell_box, sample_bgr in zip(cell_boxes, cell_samples):
		x1, y1, x2, y2 = cell_box
		cx = (x1 + x2) // 2
		cy = (y1 + y2) // 2
		radius = max(10, min((x2 - x1), (y2 - y1)) // 6)

		label = classify_bgr_color(sample_bgr)
		circle_color = label_to_bgr.get(label, (0, 0, 0))

		cv2.circle(frame, (cx, cy), radius, circle_color, -1)
		cv2.circle(frame, (cx, cy), radius, (255, 255, 255), 2)

		text_y = y2 - 8
		cv2.putText(
			frame,
			label,
			(x1 + 6, text_y),
			cv2.FONT_HERSHEY_SIMPLEX,
			0.5,
			(255, 255, 255),
			2,
			cv2.LINE_AA,
		)

		cv2.putText(
			frame,
			label,
			(x1 + 6, text_y),
			cv2.FONT_HERSHEY_SIMPLEX,
			0.5,
			(20, 20, 20),
			1,
			cv2.LINE_AA,
		)


def draw_solution_overlay(frame, status: str, solution_text: str, is_error: bool):
	panel_margin = 20
	panel_x = panel_margin
	panel_w = frame.shape[1] - panel_margin * 2
	panel_h = 96
	panel_bottom = frame.shape[0] - 48
	panel_y = panel_bottom - panel_h

	overlay = frame.copy()
	cv2.rectangle(overlay, (panel_x, panel_y), (panel_x + panel_w, panel_y + panel_h), (30, 30, 30), -1)
	frame[:] = cv2.addWeighted(overlay, 0.55, frame, 0.45, 0)

	status_color = (0, 255, 0) if not is_error else (0, 0, 255)
	cv2.putText(
		frame,
		status,
		(panel_x + 12, panel_y + 32),
		cv2.FONT_HERSHEY_SIMPLEX,
		0.72,
		status_color,
		2,
		cv2.LINE_AA,
	)

	cv2.putText(
		frame,
		solution_text,
		(panel_x + 12, panel_y + 68),
		cv2.FONT_HERSHEY_SIMPLEX,
		0.63,
		(255, 255, 255),
		2,
		cv2.LINE_AA,
	)
