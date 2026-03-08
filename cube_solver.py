import cv2
import numpy as np
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
	FACE_COUNT
)
from solving_logic import (
	scanned_faces_correct
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
				scanned_faces_correct(captured_faces)

	cap.release()
	cv2.destroyAllWindows()


if __name__ == "__main__":
	main()
