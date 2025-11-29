import numpy as np
from enum import Enum, auto


class STANCE(Enum):
    EARLY = auto()
    MIDDLE = auto()
    LATE = auto()
    SWING = auto()


# Default constants for GaitPhase
DEFAULT_DATARATE = 100
DEFAULT_LAST_STANCE_TIME = 0.6
GYROMAG_THRESHOLD_HEELSTRIKE = 45  # unit: degree
GYROMAG_THRESHOLD_TOEOFF = 45  # unit: degree
HEELSTRIKE_ITERS_THRESHOLD_FACTOR = 0.1  # 0.1s
MIN_STANCE_TIME = 0.4
MAX_STANCE_TIME = 2.0


class GaitPhase:

    def __init__(self, datarate=DEFAULT_DATARATE):
        """
        This class is to Calculate the gait phase
        @input: datarate, the update rate, unit is Hz.
        """

        self.DATARATE = datarate
        # start at default stance time, will update each step
        self.last_stance_time = DEFAULT_LAST_STANCE_TIME
        self._update_phase_thresholds()
        self.GYROMAG_THRESHOLD_HEELSTRIKE = GYROMAG_THRESHOLD_HEELSTRIKE
        self.GYROMAG_THRESHOLD_TOEOFF = GYROMAG_THRESHOLD_TOEOFF
        self.HEELSTRIKE_ITERS_THRESHOLD = HEELSTRIKE_ITERS_THRESHOLD_FACTOR * datarate

        self.gaitphase = STANCE.LATE
        self.gaitphase_old = STANCE.LATE
        self.step_count = 0
        self.iters_consecutive_below_gyroMag_thresh = 0
        self.iters_stance = 0

        self.in_feedback_window = False

        self.FPA_buffer = []
        self.FPA_this_frame = 0
        self.FPA_this_step = 0

    def update_gaitphase(self, sensor_data):
        gyro_magnitude = np.linalg.norm(
            [sensor_data["GyroX"], sensor_data["GyroY"], sensor_data["GyroZ"]],
            ord=2,
        )
        if self.gaitphase == STANCE.SWING:
            self.gaitphase_old = STANCE.SWING
            if gyro_magnitude < self.GYROMAG_THRESHOLD_HEELSTRIKE:
                # If the gyro_magnitude below than the threshold for a certain time,
                # change gaitphase to stance.
                self.iters_consecutive_below_gyroMag_thresh += 1
                if (
                    self.iters_consecutive_below_gyroMag_thresh
                    > self.HEELSTRIKE_ITERS_THRESHOLD
                ):
                    self.iters_consecutive_below_gyroMag_thresh = 0
                    self.iters_stance = 0
                    self.step_count += 1
                    self.gaitphase = STANCE.EARLY
            else:
                # If the gyro_magnitude larger than the threshold, reset the timer
                self.iters_consecutive_below_gyroMag_thresh = 0
        elif self.gaitphase == STANCE.EARLY:
            self.gaitphase_old = STANCE.EARLY
            self.iters_stance += 1
            # If the timer longer than a threshold, change gaitphase to late stance
            if self.iters_stance > self.MIDDLESTANCE_ITERS_THRESHOLD:
                self.gaitphase = STANCE.MIDDLE
        elif self.gaitphase == STANCE.MIDDLE:
            self.gaitphase_old = STANCE.MIDDLE
            self.iters_stance += 1
            if self.iters_stance > self.LATESTANCE_ITERS_THRESHOLD:
                self.gaitphase = STANCE.LATE
        elif self.gaitphase == STANCE.LATE:
            self.gaitphase_old = STANCE.LATE
            self.iters_stance += 1
            # If the gyro_magnitude larger than the threshold, change gaitphase to swing.
            if gyro_magnitude > self.GYROMAG_THRESHOLD_TOEOFF:
                self.last_stance_time = self.iters_stance / self.DATARATE
                if self.last_stance_time > MAX_STANCE_TIME:
                    self.last_stance_time = MAX_STANCE_TIME
                elif self.last_stance_time < MIN_STANCE_TIME:
                    self.last_stance_time = MIN_STANCE_TIME
                self._update_phase_thresholds()
                self.gaitphase = STANCE.SWING

        self.in_feedback_window = (
            self.gaitphase_old == STANCE.MIDDLE and self.gaitphase == STANCE.LATE
        )

    def _update_phase_thresholds(self):
        # 25% and 50% of the most recent stance duration
        self.MIDDLESTANCE_ITERS_THRESHOLD = self.last_stance_time * 0.25 * self.DATARATE
        self.LATESTANCE_ITERS_THRESHOLD = self.last_stance_time * 0.5 * self.DATARATE
