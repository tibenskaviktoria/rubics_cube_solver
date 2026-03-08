import cv2
from typing import Any
from helper_functions import (
	get_fixed_cube_guide,
	get_cell_boxes,
	draw_fixed_2x2_guide,
	print_console_instructions,
	draw_instructions,
	draw_hint,
	print_scanned_faces_summary,
	sample_cell_bgr,
	classify_bgr_color,
	draw_cell_color_markers,
	draw_solution_overlay,
	FACE_COUNT
)
from solving_logic import (
	get_cube_solution
)


def main():
	cap = cv2.VideoCapture(1)
	if not cap.isOpened():
		raise RuntimeError("Could not open camera. Check webcam permissions and camera index.")

	cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
	cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)

	print_console_instructions()

	captured_faces: list[Any] = [None] * FACE_COUNT
	captured_count = 0
	scanning_active = False
	status_text = "Press S to begin scanning"
	status_color = (0, 255, 0)
	solution_status = ""
	solution_text = ""
	solution_is_error = False

	while True:
		ok, frame = cap.read()
		if not ok:
			break

		guide_box = get_fixed_cube_guide(frame.shape, guide_ratio=0.38)
		cell_boxes = get_cell_boxes(guide_box)
		live_samples = [sample_cell_bgr(frame, cell) for cell in cell_boxes]

		draw_fixed_2x2_guide(frame, guide_box)
		draw_cell_color_markers(frame, cell_boxes, live_samples)
		draw_instructions(frame, captured_count)
		draw_hint(frame, captured_count, status_text, status_color)
		if solution_status:
			draw_solution_overlay(frame, solution_status, solution_text, solution_is_error)
		cv2.imshow("2x2 Rubik Cube Manual Scan", frame)

		key = cv2.waitKey(1) & 0xFF
		if key == ord("q"):
			break

		if key == ord("s"):
			captured_faces = [None] * FACE_COUNT
			captured_count = 0
			scanning_active = True
			status_text = "Scanning started. Press SPACE to save current face"
			status_color = (0, 255, 255)
			solution_status = ""
			solution_text = ""
			solution_is_error = False
			print("=== Scan Started ===")

		if key == 32 and scanning_active: # SPACE key to capture current face
			if captured_count >= FACE_COUNT:
				status_text = "All 6 faces already scanned. Press S to restart"
				status_color = (255, 255, 0)
				continue

			face_sample = [
				{"bgr": sample, "label": classify_bgr_color(sample)} for sample in live_samples
			]
			print(f"Captured face {captured_count + 1}: {[cell['label'] for cell in face_sample]}")
			captured_faces[captured_count] = face_sample
			captured_count += 1
			status_text = f"Captured face {captured_count} ({captured_count}/{FACE_COUNT})"
			status_color = (0, 255, 0)

			if captured_count >= FACE_COUNT:
				status_text = "6 faces captured. Scan complete"
				status_color = (255, 255, 0)
				scanning_active = False
				print_scanned_faces_summary(captured_faces)
				ret, computed_solution = get_cube_solution(captured_faces)
				if ret:
					solution_length = len(computed_solution.split())
					if solution_length < 1:
						print("The cube is already solved! No moves needed.")
						solution_status = "Solved"
						solution_text = "The cube is already solved. No moves needed."
						solution_is_error = False
					else:
						solution_status = f"Solution found ({solution_length} moves)"
						solution_text = computed_solution
						solution_is_error = False
					print(f"Found solution of length {solution_length}: {computed_solution}")
				else:
					print("Error:", computed_solution)
					solution_status = "Solver error"
					solution_text = str(computed_solution)
					solution_is_error = True
				print("=== Scan Complete ===\n")

	cap.release()
	cv2.destroyAllWindows()


if __name__ == "__main__":
	main()
