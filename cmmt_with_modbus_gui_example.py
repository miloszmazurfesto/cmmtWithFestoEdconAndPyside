# Importing the Festo edcon library
from edcon.edrive.com_modbus import ComModbus
from edcon.edrive.motion_handler import MotionHandler
from edcon.utils.logging import Logging

# Importing PySide6 library - used for creating gui with QT in Python
from PySide6 import QtCore, QtWidgets

# Importing utility libraries
import ipaddress
import sys

# Enabling robust logging in the CMD console 
Logging()

# Creation of the MainWindow class that handles GUI and underlying logic
class MainWindow(QtWidgets.QWidget):
    # Constructor of the class, taking edrive as parameter
    def __init__(self, _edrive):
        # Running the constructor of base class
        super().__init__()

        # Saving reference to parameter passed in the constructor
        self.edrive = _edrive
        
        # Setting the title of the window
        self.setWindowTitle("CMMT PC Control")

        # Initializing the GUI elements like buttons or labels.
        self.ipAddressLabel           = QtWidgets.QLabel("Ip address of CMMT:")
        self.ipAddressTextInput       = QtWidgets.QTextEdit("192.168.0.1")
        self.connectToCmmtButton      = QtWidgets.QPushButton("Connect to CMMT")
        self.acknowdlegeErrorsButton  = QtWidgets.QPushButton("Acknowledge errors")
        self.powerDisableButton       = QtWidgets.QPushButton("Disable powerstage")
        self.referenceDriveButton     = QtWidgets.QPushButton("Home drive")
        self.jogPositiveButton        = QtWidgets.QPushButton("Jog Positive")
        self.jogNegativeButton        = QtWidgets.QPushButton("Jog Negative")
        self.jogPositiveTimer         = QtCore.QTimer()
        self.jogNegativeTimer         = QtCore.QTimer()
        self.movetoPositionLabel      = QtWidgets.QLabel("Move to positions controls:")
        self.absoluteMovementCheckbox = QtWidgets.QCheckBox("Absolute movement")
        self.positionLabel            = QtWidgets.QLabel("Position to move to (mm):")
        self.positionValue            = QtWidgets.QTextEdit("200")
        self.velocityLabel            = QtWidgets.QLabel("Movement velocity (mm/s):")
        self.velocityValue            = QtWidgets.QTextEdit("100")
        self.moveToPositionButton     = QtWidgets.QPushButton("Move to position")

        # Setting height of the Text Input Fields
        self.ipAddressTextInput.setFixedHeight(20)
        self.positionValue.setFixedHeight(20)
        self.velocityValue.setFixedHeight(20)

        # Initializing layouts that will contain GUI elements
        verticalBoxControls  = QtWidgets.QVBoxLayout()
        joggingButtonsLayout = QtWidgets.QHBoxLayout()
        horizontalBox        = QtWidgets.QHBoxLayout()
        
        # Adding GUI Elements to Layouts and builiding Layout hierarchy 
        verticalBoxControls.addWidget(self.ipAddressLabel)
        verticalBoxControls.addWidget(self.ipAddressTextInput)
        verticalBoxControls.addWidget(self.connectToCmmtButton)
        verticalBoxControls.addWidget(self.acknowdlegeErrorsButton)
        verticalBoxControls.addWidget(self.powerDisableButton)
        verticalBoxControls.addWidget(self.referenceDriveButton)
        joggingButtonsLayout.addWidget(self.jogNegativeButton)
        joggingButtonsLayout.addWidget(self.jogPositiveButton)
        verticalBoxControls.addLayout(joggingButtonsLayout)
        verticalBoxControls.addWidget(self.movetoPositionLabel)
        verticalBoxControls.addWidget(self.absoluteMovementCheckbox)
        verticalBoxControls.addWidget(self.positionLabel)
        verticalBoxControls.addWidget(self.positionValue)
        verticalBoxControls.addWidget(self.velocityLabel)
        verticalBoxControls.addWidget(self.velocityValue)
        verticalBoxControls.addWidget(self.moveToPositionButton)
        horizontalBox.addLayout(verticalBoxControls)

        # Setting the layout of the main window
        self.setLayout(horizontalBox)

        # Connecting the corresponding functions to the correct butttons being clicked
        self.connectToCmmtButton    .clicked.connect(self.connectToCMMT)
        self.acknowdlegeErrorsButton.clicked.connect(self.acknowledgeErrors)
        self.powerDisableButton     .clicked.connect(self.disablePowerstage)
        self.referenceDriveButton   .clicked.connect(self.referenceCMMT)
        self.moveToPositionButton   .clicked.connect(self.moveToPosition)

        # Handling of the jog positive button - calling jog task periodically each 200ms  
        self.jogPositiveButton.pressed .connect(self.onJogPositiveClicked)
        self.jogPositiveButton.released.connect(self.onJogPositiveReleased)
        self.jogPositiveTimer.timeout  .connect(self.onEvery200MSJogPositivePressed)

        # Handling of the jog negative button - calling jog task periodically each 200ms  
        self.jogNegativeButton.pressed .connect(self.onJogNegativeClicked)
        self.jogNegativeButton.released.connect(self.onJogNegativeReleased)
        self.jogNegativeTimer.timeout  .connect(self.onEvery200MSJogNegativePressed)

        
    # Method that handles connecting to CMMT with Modbus TCP/IP comm protocol
    @QtCore.Slot()
    def connectToCMMT(self):
        # Acquiring the IP Adress from the text input
        ip_string = self.ipAddressTextInput.toPlainText()

        # Checking whether the ip string got the correct format
        try:
            ip_object = ipaddress.ip_address(ip_string)
        except ValueError:
            print("The IP address '{ip_string}' is not valid")   
            return
        
        # Establishing modbus connection with ComModbus class using given ip address and default timemout value
        self.edrive = ComModbus(ip_string)

        # Initializing the instance of MotionHandler class required for reading and writing data Telegram 111 data frames
        # that are exchanged through Modbus TCP connection.
        self.motionHandler = MotionHandler(self.edrive)

        # Enabling continous updates required for smooth jogging
        self.motionHandler.configure_continuous_update(True)

    # Method that allows for error acknowledgement
    @QtCore.Slot()
    def acknowledgeErrors(self):
        # Check whether edrive is of ComModbus type - if true, the connection is established 
        if(not isinstance(self.edrive, ComModbus)):
            return

        # Acknowledge errors with MotionHandler class method
        self.motionHandler.acknowledge_faults()

    # Method that allows to disable power stage if necessary
    @QtCore.Slot()
    def disablePowerstage(self):
        # Check whether edrive is of ComModbus type - if true, the connection is established 
        if(not isinstance(self.edrive, ComModbus)):
            return
        
        # Disable power with MotionHandler class method 
        self.motionHandler.disable_powerstage()
            

    # Method that allows to reference the drive - the homing method defined during configuration
    # of the servo-drive in Festo Automation Suite is used
    @QtCore.Slot()
    def referenceCMMT(self):
        # Check whether edrive is of ComModbus type - if true, the connection is established 
        if(not isinstance(self.edrive, ComModbus)):
            return

        # Enable the powerstage of the CMMT with MotionHandler class method 
        self.motionHandler.enable_powerstage()

        # Perform referencing procedure with MotionHandler class method
        self.motionHandler.referencing_task()
    

    # After pressing jog positive button enable powerstage, perform jog function and start timer
    # that will execute the same function after it finishes counting the 200MS. This will continue
    # until the button is pressed.
    @QtCore.Slot()
    def onJogPositiveClicked(self):
        self.motionHandler.enable_powerstage()
        self.jogFunction(True)
        self.jogPositiveTimer.start(200)

    @QtCore.Slot()
    def onEvery200MSJogPositivePressed(self):
        self.jogFunction(True)
        
    # After the jog positive button is released, stop the motion, disable power and stop the timer 
    @QtCore.Slot()
    def onJogPositiveReleased(self):
        self.motionHandler.stop_motion_task()
        self.motionHandler.disable_powerstage()
        self.jogPositiveTimer.stop()

    # Analogous function as for the jog positive button but for the jog negative button
    @QtCore.Slot()
    def onJogNegativeClicked(self):
        self.motionHandler.enable_powerstage()
        self.jogFunction(False)
        self.jogNegativeTimer.start(200)

    @QtCore.Slot()
    def onEvery200MSJogNegativePressed(self):
        self.jogFunction(False)        

    @QtCore.Slot()
    def onJogNegativeReleased(self):
        self.motionHandler.stop_motion_task()
        self.motionHandler.disable_powerstage()
        self.jogNegativeTimer.stop()


    # Method that allows to perform the jog task
    def jogFunction(self, direction):
        # Check whether edrive is of ComModbus type - if true, the connection is established 
        if(not isinstance(self.edrive, ComModbus)):
            return
        
        # Checking whether the drive is ready for motion with correct method of MotionHandler class
        if(not self.motionHandler.ready_for_motion):
            return  
        
        # Perform the jog task with duration equal to 0.0 so that a nonblocking feature can be achieved.
        # which will result in smooth motion after holding the button. 
        self.motionHandler.jog_task(direction, not direction, duration=0.0)

    # Methods that allow for movements to specified either absolute or relative positions.
    @QtCore.Slot()
    def moveToPosition(self):
        # Take the position and velocity from the text inputs, cast them to integers and rescale to fit 
        # the -6 factor set in the Factor Group during commisioning of the drive in Festo Automation Suite
        positionToMoveTo   = int(self.positionValue.toPlainText()) * 1000
        velocityToMoveWith = int(self.velocityValue.toPlainText()) * 1000

        # Checking whether the move should be absolute or relative
        isMoveAbsolute = self.absoluteMovementCheckbox.isChecked()

        # Check whether edrive is of ComModbus type - if true, the connection is established 
        if(not isinstance(self.edrive, ComModbus)):
            return

        # Checking whether the drive is ready for motion with correct method of MotionHandler class
        if(not self.motionHandler.ready_for_motion):
            return  
        
        # Enable the powerstage of the CMMT with MotionHandler class method 
        self.motionHandler.enable_powerstage()

        # Performing the position task with specified previously parameters
        self.motionHandler.position_task(positionToMoveTo, velocityToMoveWith, isMoveAbsolute)
    
# Main runtime of the application that creates and displays the GUI prepared in the MainWindow class
if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    drive = None
    mainWindow = MainWindow(drive)
    mainWindow.show()
    sys.exit(app.exec_())