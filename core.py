import time
from sage.base_app import BaseApp
from .gaitphase import GaitPhase, STANCE
from .FSA_algorithm import FootSagittalAngle

# Constants for feedback state
FEEDBACK_ON = 1
FEEDBACK_OFF = 0


class Core(BaseApp):
    ###########################################################
    # INITIALIZE APP
    ###########################################################
    def __init__(self, my_sage):
        BaseApp.__init__(self, my_sage, __file__)

        # Constants
        self.DATARATE = self.info["datarate"]
        self.PULSE_LENGTH = float(self.config["pulse_length"])

        # Node indices
        self.NODENUM_SENSOR_FOOT_LEFT = self.info["sensors"].index("foot_left")
        self.NODENUM_SENSOR_FOOT_RIGHT = self.info["sensors"].index("foot_right")
        self.NODENUM_FEEDBACK_SHANK_LEFT = self.info["feedback"].index("shank_left")
        self.NODENUM_FEEDBACK_SHANK_RIGHT = self.info["feedback"].index("shank_right")

        # Initiate GaitPhase subclasses
        self.my_GP_left = GaitPhase(datarate=self.info["datarate"])
        self.my_GP_right = GaitPhase(datarate=self.info["datarate"])

        # Initiate variables
        self.iteration = 0
        self.Feedback_Left = 0
        self.Feedback_Right = 0
        self.feedback_left_TimeSinceFeedbackStarted = 0
        self.feedback_right_TimeSinceFeedbackStarted = 0
        self.feedback_left_active = False
        self.feedback_right_active = False
        self.left_fsa = FootSagittalAngle()
        self.right_fsa = FootSagittalAngle()

    ###########################################################
    # CHECK NODE CONNECTIONS
    ###########################################################
    def check_status(self):
        sensors_count = self.get_sensors_count()
        feedback_count = self.get_feedback_count()
        err_msg = ""
        if sensors_count < len(self.info["sensors"]):
            err_msg += "Algorithm requires {} sensors but only {} are connected".format(
                len(self.info["sensors"]), sensors_count
            )
        if feedback_count < len(self.info["feedback"]):
            err_msg += "Algorithm require {} feedback but only {} are connected".format(
                len(self.info["feedback"]), feedback_count
            )
        if err_msg != "":
            return False, err_msg
        return True, "Now app is running"

    ###########################################################
    # RUN APP IN LOOP
    ###########################################################
    def run_in_loop(self):
        data = self.my_sage.get_next_data()

        # Compute sagittal foot angles via FootSagittalAngle estimators (Will be 0 the first time due to calibration)
        left_foot_data = data[self.NODENUM_SENSOR_FOOT_LEFT]
        right_foot_data = data[self.NODENUM_SENSOR_FOOT_RIGHT]

        self.left_fsa.update_FSA(left_foot_data)
        self.right_fsa.update_FSA(right_foot_data)

        # Compute gait phases
        self.my_GP_left.update_gaitphase(left_foot_data)
        self.my_GP_right.update_gaitphase(right_foot_data)

        # Add time from 1 timestep to timers
        self.feedback_left_TimeSinceFeedbackStarted += 1 / self.DATARATE
        self.feedback_right_TimeSinceFeedbackStarted += 1 / self.DATARATE

        # Compute foot angular velocities in the sagittal plane
        left_foot_sag_ang_vel = left_foot_data["GyroX"]
        right_foot_sag_ang_vel = right_foot_data["GyroX"]

        if self.config["left_feedback_enabled"]:
            self.Feedback_Left = self.give_feedback(
                self.my_GP_left,
                self.NODENUM_FEEDBACK_SHANK_LEFT,
                self.feedback_left_TimeSinceFeedbackStarted,
            )

        if self.config["right_feedback_enabled"]:
            self.Feedback_Right = self.give_feedback(
                self.my_GP_right,
                self.NODENUM_FEEDBACK_SHANK_RIGHT,
                self.feedback_right_TimeSinceFeedbackStarted,
            )

        time_now = self.iteration / self.DATARATE  # time in seconds

        my_data = {
            "time": [time_now],
            "Left_Foot_Sag_Ang_Vel": [left_foot_sag_ang_vel],
            "Left_Foot_Sag_Angle": [self.left_fsa.normalized_angle],
            "Gait_Phase_Left": [self.my_GP_left.gaitphase.value],
            "Right_Foot_Sag_Ang_Vel": [right_foot_sag_ang_vel],
            "Right_Foot_Sag_Angle": [self.right_fsa.normalized_angle],
            "Gait_Phase_Right": [self.my_GP_right.gaitphase.value],
            "Feedback_Left": [self.Feedback_Left],
            "Feedback_Right": [self.Feedback_Right],
        }

        # Increment and save data
        self.iteration += 1
        self.my_sage.save_data(data, my_data)
        self.my_sage.send_stream_data(data, my_data)
        return True

    ###########################################################
    # MANAGE FEEDBACK FOR APP
    ###########################################################
    def give_feedback(self, gait_phase_obj, node_num, time_since_start):
        is_left = node_num == self.NODENUM_FEEDBACK_SHANK_LEFT
        is_right = node_num == self.NODENUM_FEEDBACK_SHANK_RIGHT
        if not (is_left or is_right):
            raise ValueError("Unknown feedback node {}".format(node_num))

        feedback_active = (
            self.feedback_left_active if is_left else self.feedback_right_active
        )

        should_feedback = False
        if self.config["whenFeedback"] == "Early, Middle and Late stance":
            # Note: Do not provide feedback during swing gait phase
            if (
                gait_phase_obj.gaitphase_old != gait_phase_obj.gaitphase
                and gait_phase_obj.gaitphase != STANCE.SWING
            ):
                should_feedback = True
        else:
            if (
                gait_phase_obj.gaitphase_old == STANCE.SWING
                and gait_phase_obj.gaitphase == STANCE.EARLY
            ):
                should_feedback = True

        if should_feedback:
            self.toggle_feedback(
                node_num, duration=self.PULSE_LENGTH, feedback_state=True
            )
            if is_left:
                self.feedback_left_TimeSinceFeedbackStarted = 0
                self.feedback_left_active = True
            else:
                self.feedback_right_TimeSinceFeedbackStarted = 0
                self.feedback_right_active = True
            return FEEDBACK_ON

        if feedback_active and time_since_start > self.PULSE_LENGTH:
            self.toggle_feedback(node_num, feedback_state=False)
            if is_left:
                self.feedback_left_active = False
            else:
                self.feedback_right_active = False
            return FEEDBACK_OFF

        return FEEDBACK_ON if feedback_active else FEEDBACK_OFF

    def toggle_feedback(self, feedbackNode=0, duration=1, feedback_state=False):
        if feedback_state:
            self.my_sage.feedback_on(feedbackNode, duration)
        else:
            self.my_sage.feedback_off(feedbackNode)
