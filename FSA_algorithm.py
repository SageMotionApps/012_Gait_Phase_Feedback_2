from typing import Optional
from .Rotation import Rotation as R


def _normalize_angle(angle_deg: float) -> float:
    """Wrap an angle in degrees to the range [-180, 180)."""
    return (angle_deg + 180.0) % 360.0 - 180.0

class FootSagittalAngle:
    """
    Estimate the sagittal-plane foot angle (toes up/down) from a foot IMU.

    The class keeps track of a standing reference collected from the first
    available frame and reports global foot angle relative
    to that baseline.
    """

    def __init__(self):
        """
        This class is to Calculate the Global Foot Angle in the Sagittal Plane.
        """

        self.reference_roll: Optional[float] = None
        self.normalized_angle: float = 0.0

    def update_FSA(self, sensor_data: dict) -> float:
        """
        Update the sagittal angle estimate using the latest sensor sample.

        Args:
            sensor_data (dict): Dictionary containing quaternion keys Quat1..Quat4.

        Returns:
            float: Filtered sagittal-plane angle in degrees
                   (positive = toes up / dorsiflexion).
        """
        fsa_quat = R.from_quat(
            [
                sensor_data["Quat1"],
                sensor_data["Quat2"],
                sensor_data["Quat3"],
                sensor_data["Quat4"],
            ],
            scalar_first=True,
        )
        rotation = fsa_quat.as_euler("ZYX", degrees=True)[2]
        print(f"Rotation ZYX: {rotation}")
        roll = _normalize_angle(rotation)

        if self.reference_roll is None:
            self.reference_roll = roll

        self.normalized_angle = _normalize_angle(roll - self.reference_roll)

        return self.normalized_angle
