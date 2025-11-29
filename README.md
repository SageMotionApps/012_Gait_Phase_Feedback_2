# 012 Gait Phase Feedback 2
Compute foot sagittal angles and angular velocities for both feet and deliver timed feedback during stance.

### Nodes Required: 4 
 - Sensing (2): `foot_left`, `foot_right` (top of foot, switch pointing forward) 
 - Feedback (2): 
    - `shank_left`: Haptic feedback when the left foot reaches the configured stance phase.
    - `shank_right`: Haptic feedback when the right foot reaches the configured stance phase.

## Algorithm & Calibration
### Algorithm Information
The app samples both foot IMUs at 100 Hz. Each update converts the IMU quaternion to Euler angles and extracts the roll component to represent sagittal foot angle. The gait phase (swing, early stance, mid stance, late stance) is calculated for each foot, and during transitions between gait phases, feedback is triggered for a user-set pulse duration. Currently, the app supports providing feedback at one of the following transition sets:  
- swing → early stance  
- All transitions except for late stance → swing  

### Calibration Process:
The first available quaternion sample sets the standing reference roll for each foot; subsequent angles are reported relative to this baseline. No additional manual alignment is performed.

## Description of Data in Downloaded File

### Calculated Fields
| Field Name               | Description                                                                              |
|--------------------------|------------------------------------------------------------------------------------------|
| `time`                   | Time since trial start (sec)                                                             |
| `Left_Foot_Sag_Ang_Vel`  | Left foot sagittal-plane angular velocity from GyroX (deg/s)                             |
| `Left_Foot_Sag_Angle`    | Left foot sagittal-plane angle relative to initial reference (deg)                       |
| `Gait_Phase_Left`        | Gait phase for left leg (0: swing, 1: early stance, 2: mid stance, 3: late stance).      |
| `Right_Foot_Sag_Ang_Vel` | Right foot sagittal-plane angular velocity from GyroX (deg/s)                            |
| `Right_Foot_Sag_Angle`   | Right foot sagittal-plane angle relative to initial reference (deg)                      |
| `Gait_Phase_Right`       | Gait phase for right leg (0: swing, 1: early stance, 2: mid stance, 3: late stance).     |
| `Feedback_Left`          | Feedback status for `shank_left` node (0 = off, 1 = on)                                  |
| `Feedback_Right`         | Feedback status for `shank_right` node (0 = off, 1 = on)                                 |

### Sensor Raw Data Values
> Note: The following data fields are repeated for each foot sensor (`_1` = left, `_2` = right).

| Field Name          | Description                             |
|---------------------|-----------------------------------------|
| `SensorIndex_1/2`   | Index of raw sensor data                |
| `AccelX/Y/Z_1/2`    | Raw acceleration data (m/s²)            |
| `GyroX/Y/Z_1/2`     | Raw gyroscope data (deg/s)              |
| `MagX/Y/Z_1/2`      | Raw magnetometer data (μT)              |
| `Quat1/2/3/4_1/2`   | Quaternion data (scalar-first order)    |
| `Sampletime_1/2`    | Timestamp of the sensor value           |
| `Package_1/2`       | Package number of the sensor value      |

---

## File Output
Data is saved automatically after the session using the specified format (`csv`, `h5`, or `xlsx`). You can find your results under the **Download Data** section after clicking `Stop`.

---

## More Information
See the full guide: **Gait Phase Feedback 2 App Guide.pdf**


## Development and App Processing Loop
The best place to start with developing an or modifying an app, is the [SageMotion Documentation](http://docs.sagemotion.com/index.html) page.