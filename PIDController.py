import math


class PIDController:
    """
    Improved positional PID controller
    (anti-integral-windup + derivative filtering + output limiting)
    """

    def __init__(self, sample_time, kp, ki, kd, max_adjust=100, min_adjust=-100):

        # basic parameters
        self.sample_time = sample_time
        self.kp = kp
        self.ki = ki
        self.kd = kd

        self.integral_sum = 0
        self.last_error = 0
        self.current_error = 0

        # output limits
        self.max_adjust = max_adjust
        self.min_adjust = min_adjust

        # derivative filter
        self.derivative_filter_ratio = 0.2
        self.last_derivative = 0

        # integral limit
        if ki != 0 and sample_time != 0:
            self.integral_limit = abs(max_adjust - min_adjust) / (ki * sample_time)
        else:
            self.integral_limit = 1000
        self.smooth_ratio = 0.45
        self.last_output = 0     

    def _pid_core_calculate(self, target_value, current_value):

        if self.sample_time <= 0:
            raise ValueError("sample_time must be greater than 0")

        # error
        self.current_error = target_value - current_value

        # P
        p_term = self.kp * self.current_error

        # I
        self.integral_sum += self.current_error * self.sample_time
        self.integral_sum = max(min(self.integral_sum, self.integral_limit), -self.integral_limit)
        i_term = self.ki * self.integral_sum

        # D
        derivative_raw = (self.current_error - self.last_error) / self.sample_time

        self.last_derivative = (
            self.derivative_filter_ratio * derivative_raw
            + (1 - self.derivative_filter_ratio) * self.last_derivative
        )

        d_term = self.kd * self.last_derivative

        # PID output
        pid_output = p_term + i_term + d_term

        # output limit
        pid_output = max(min(pid_output, self.max_adjust), self.min_adjust)

        # update last error
        self.last_error = self.current_error

        #return int(round(pid_output, 0))
       # smoothing (anti jitter)
        smooth_output = (
            self.smooth_ratio * pid_output
            + (1 - self.smooth_ratio) * self.last_output
        )

        self.last_output = smooth_output

        return int(round(smooth_output, 0))

    def pid_position_y(self, target_y, region_height_half):
        return self._pid_core_calculate(target_y, region_height_half)

    def pid_position_x(self, target_x, region_width_half):
        return self._pid_core_calculate(target_x, region_width_half)


# global locked target info
locked_target_info = {
    "is_locked": False,
    "locked_distance": 0.0,
    "locked_target": None
}


def yolo_get_nearest_enemy_distance(
        x, y, w, h,
        aim_ratio_x, aim_ratio_y,
        region_width_half,
        region_height_half):

    center_x = round(x + w * aim_ratio_x, 1)
    center_y = round(y + h * aim_ratio_y, 1)

    offset_x = round(center_x - region_width_half, 10)
    offset_y = round(center_y - region_height_half, 10)

    distance = round(math.sqrt(offset_x ** 2 + offset_y ** 2), 1)

    return distance


def select_and_lock_nearest_target(
        target_list,
        aim_ratio_x,
        aim_ratio_y,
        region_width_half,
        region_height_half,
        distance_dead_zone=5.0,
        switch_threshold=0.2):

    global locked_target_info

    target_distance_list = []

    for target in target_list:
        x, y, w, h = target

        distance = yolo_get_nearest_enemy_distance(
            x, y, w, h,
            aim_ratio_x,
            aim_ratio_y,
            region_width_half,
            region_height_half
        )

        target_distance_list.append((distance, target))

    if not target_distance_list:

        locked_target_info["is_locked"] = False
        locked_target_info["locked_target"] = None

        return None

    target_distance_list.sort(key=lambda x: x[0])

    nearest_distance, nearest_target = target_distance_list[0]

    if not locked_target_info["is_locked"]:

        locked_target_info["is_locked"] = True
        locked_target_info["locked_distance"] = nearest_distance
        locked_target_info["locked_target"] = nearest_target

    else:

        locked_distance = locked_target_info["locked_distance"]

        distance_diff = locked_distance - nearest_distance

        ratio_diff = (locked_distance - nearest_distance) / max(locked_distance, 1e-6)

        need_switch = (distance_diff > distance_dead_zone) and (ratio_diff > switch_threshold)

        locked_target_exists = locked_target_info["locked_target"] in [t[1] for t in target_distance_list]

        if not locked_target_exists or need_switch:

            locked_target_info["locked_distance"] = nearest_distance
            locked_target_info["locked_target"] = nearest_target

        else:

            nearest_target = locked_target_info["locked_target"]

    return nearest_target


def distance_between_points(x1, y1, x2, y2):

    return math.sqrt((x1 - x2) ** 2 + (y1 - y2) ** 2)