import cv2


class GestionnaireCamera:
	def __init__(self, config):
		self.config=config
		self.cap= None

	def open(self):
		self.cap= cv2.VideoCapture(self.camera_id)
		if not self.cap.isOpened():
			return False

		self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.config.largeur)
                self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.config.hauteur)
		return True

	def read(self):
		if self.cap is None or not self.cap.isOpened():
			return None
		ret, frame=self.cap.read()

		if not ret:
			return None

		return frame

	def release(self):
		if self.cap is not None:
			self.cap.release()
