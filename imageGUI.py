import sys
import image
import time
import requests
import traceback
from PyQt5.QtWidgets import (QDialog, QGroupBox, QLineEdit, QTextEdit, QMainWindow,QWidget,
	QPushButton, QLabel,QApplication, QVBoxLayout, QGridLayout, QCheckBox)
from PyQt5.QtGui import QIcon, QImage, QPalette, QPixmap
from PyQt5.QtCore import QObject, Qt,QRunnable, QThreadPool, pyqtSignal, pyqtSlot, QEvent

class WorkerSignals(QObject):
	finished = pyqtSignal()
	error = pyqtSignal(tuple)
	result = pyqtSignal(object)
	progress = pyqtSignal(int)

class Worker(QRunnable):

	def __init__(self, fn, *args, **kwargs):
		super(Worker, self).__init__()

		# Store constructor arguments (re-used for processing)
		self.fn = fn
		self.args = args
		self.kwargs = kwargs
		self.signals = WorkerSignals()

	@pyqtSlot()
	def run(self):
		try:
			result = self.fn(*self.args, **self.kwargs)
		except:
			traceback.print_exc()
			exctype, value = sys.exc_info()[:2]
			self.signals.error.emit((exctype, value, traceback.format_exc()))
		else:
			self.signals.result.emit(result)  # Return the result of the processing
		finally:
			self.signals.finished.emit()  # Done
			print(self.signals.finished.emit())

class imageMainWindow(QMainWindow):

	def __init__(self, parent=None):
		super(imageMainWindow, self).__init__(parent)
		self.form_widget = ImageViewer(self)
		self.left = 10
		self.top = 10
		self.width = 500
		self.height = 700
		self.title = 'Image Viewer'
		self.initUI()
		self.setCentralWidget(self.form_widget)

	def initUI(self):
		self.setWindowTitle(self.title)
		self.setGeometry(self.left, self.top, self.width, self.height)
		#Icons made Freepik
		self.setWindowIcon(QIcon(QPixmap(('./gallery.png'))))

class ImageViewer(QWidget):

	def __init__(self, parent):
		super(ImageViewer,self).__init__(parent)
		self.imagelist = []
		self.userAction = -1  # 0 - stopped, 1 - playing
		self.count = 0
		self.initUI()

	def initUI(self):
		self.createGridLayout()

		windowLayout = QVBoxLayout()
		windowLayout.addWidget(self.horizontalGroupBox)
		self.setLayout(windowLayout)
		self.buttonSanitation()

		self.show()

	def createGridLayout(self):
		#image objects
		self.image = QImage()
		self.imageLabel = QLabel()
		self.imageLabel.setBackgroundRole(QPalette.Base)

		self.searchLabel = QLabel('Search image:')
		self.linedit = QLineEdit()
		self.linedit.setPlaceholderText('cat | aww | http://boards.4channel.org/...')
		self.googleButton = QPushButton('Google')
		self.redditButton = QPushButton('Reddit')
		self.chanButton = QPushButton('4Chan')
		self.imageCountLabel = QLabel('-/-')
		self.nextButton = QPushButton('>')
		self.autoNextCb = QCheckBox('Auto next after:')
		self.timeLinedit = QLineEdit('2')
		self.timeLinedit.setFixedWidth(40)
		self.prevButton = QPushButton('<')
		self.urlLabel = QLabel('Url: ')
		self.urlLinedit = QLineEdit()
		self.threadpool = QThreadPool()

		self.horizontalGroupBox = QGroupBox()
		layout = QGridLayout()

		layout.addWidget(self.searchLabel,0,0,1,2)
		layout.addWidget(self.linedit,0,2,1,7)
		layout.addWidget(self.googleButton,1,0,1,3)
		layout.addWidget(self.redditButton,1,3,1,3)
		layout.addWidget(self.chanButton,1,6,1,3)
		layout.addWidget(self.urlLabel,2,0,1,2)
		layout.addWidget(self.urlLinedit,2,2,1,7)
		layout.addWidget(self.imageLabel,3,0,1,9)
		layout.addWidget(self.prevButton,4,0,1,2)
		layout.addWidget(self.imageCountLabel,4,2,1,1)
		layout.addWidget(self.autoNextCb,4,3,1,3)
		layout.addWidget(self.timeLinedit,4,6,1,1)
		layout.addWidget(self.nextButton,4,7,1,2)

		self.horizontalGroupBox.setLayout(layout)

		self.googleButton.clicked.connect(self.findImages)
		self.redditButton.clicked.connect(self.findImages)
		self.chanButton.clicked.connect(self.findImages)
		self.nextButton.clicked.connect(self.nextImage)
		self.prevButton.clicked.connect(self.prevImage)
		self.autoNextCb.stateChanged.connect(self.auto)

	def images_(self,userInput):
		self.count = 0

		url = self.linedit.text()
		img = image.Images()
		#uses getattr to call the right fuction from image.py depending on the button pressed by the user (google,reddit,4chan)
		self.imagelist = getattr(img, userInput)(url)
		self.imageCountLabel.setText(f'1/{len(self.imagelist)}')
		self.buttonSanitation()
		#show image in a QImage object
		self.getImages()
		
	def findImages(self):
		sender = self.sender()

		#if autonext thread is active -> stop
		if self.userAction == 1:
			self.userAction = 0

		if sender.text() == 'Reddit':
			userInput = 'Reddit'
		elif sender.text() == '4Chan':
			userInput = 'Chan'
		elif sender.text() == 'Google':
			userInput = 'Google'
		else:
			return
		# setup thread
		worker = Worker(self.images_,userInput=userInput)
		# Execute
		self.threadpool.start(worker)

	def nextImage(self):
		self.count += 1
		self.buttonSanitation()
		self.imageCountLabel.setText(f'{self.count+1}/{len(self.imagelist)}')
		self.getImages()

	def prevImage(self):
		self.count -= 1
		self.buttonSanitation()
		self.imageCountLabel.setText(f'{self.count+1}/{len(self.imagelist)}')
		self.getImages()

	def buttonSanitation(self):
		print(self.count,'/',len(self.imagelist))
		#if there is only one image disable both
		if len(self.imagelist) <= 1:
			self.prevButton.setEnabled(False)
			self.nextButton.setEnabled(False)
			return
		#prevButton -> count = 0
		if self.count <= 0:
			self.prevButton.setEnabled(False)
			self.nextButton.setEnabled(True)
		#nextButton -> count = len(self.imagelist)
		elif self.count+1 >= len(self.imagelist):
			self.prevButton.setEnabled(True)
			self.nextButton.setEnabled(False)
		else:
			self.nextButton.setEnabled(True)
			self.prevButton.setEnabled(True)

	def autoNext(self):
		lengthOfList = len(self.imagelist)

		while lengthOfList > self.count+1:
			if self.count != 0:
				time.sleep(int(self.timeLinedit.text()))

			if self.userAction == 0:
				print('Stopping')
				break

			#print(f'{self.count+1} {len(self.imagelist)} userAction: {self.userAction}')
			self.count += 1

			self.imageCountLabel.setText(f'{self.count+1}/{len(self.imagelist)}')
			self.getImages()
			print(lengthOfList,self.count+1)
			if lengthOfList == self.count+1:
				self.autoNextCb.setChecked(False)

		self.nextButton.setEnabled(True)
		self.prevButton.setEnabled(True)
		self.buttonSanitation()

	def auto(self,state):
		'''
		Checkbox -> when state is checked images slide every x seconds
		'''
		if state == Qt.Checked:
			self.nextButton.setEnabled(False)
			self.prevButton.setEnabled(False)
			#state = playing -> thread is active
			self.userAction = 1
			# Pass the function to execute
			worker = Worker(self.autoNext) # Any other args, kwargs are passed to the run function

			# Execute
			self.threadpool.start(worker)
		else:
			#stop thread
			self.userAction = 0

	def getImages(self):
		self.urlLinedit.setText(self.imagelist[self.count])
		data = requests.get(self.imagelist[self.count]).content
		self.image.loadFromData(data)
		self.pixmap = QPixmap(self.image)
		self.pix = self.pixmap.scaled(self.imageLabel.size(),Qt.KeepAspectRatio,Qt.SmoothTransformation)
		self.imageLabel.setPixmap(self.pix)
		self.imageLabel.setAlignment(Qt.AlignCenter)
		self.imageLabel.setMinimumSize(1,1)
		# Sets an evenFilter that resizes and centers the image if the label size is changed
		self.imageLabel.installEventFilter(self)

	def eventFilter(self, source, event):
		if (source is self.imageLabel and event.type() == QEvent.Resize):
			# re-scale the pixmap when the label resizes
			self.imageLabel.setPixmap(self.pixmap.scaled(
				self.imageLabel.size(), Qt.KeepAspectRatio,Qt.SmoothTransformation))
			self.imageLabel.setAlignment(Qt.AlignCenter)
		return super(ImageViewer, self).eventFilter(source, event) 

if __name__ == '__main__':

	app = QApplication(sys.argv)
	imageViewer = imageMainWindow()
	imageViewer.show()

	sys.exit(app.exec_())