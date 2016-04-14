__author__ = 'gmn255'

from TrendDetectionClass import TrendDetectionClass


class DailyGaitSpeedTrendDetection(TrendDetectionClass):
    """
    This class detects alarming trends based on the daily gaitspeed data stream
    """

    def __init__(self, datalist):
        """
        constructor
        """
        super(DailyGaitSpeedTrendDetection, self).__init__(datalist)

    def is_most_recent_trend_alarming(self, threshold=-0.0001):
        """
        Detect trends in most recent gaitspeed values
        :param threshold: value of slope below which trend should be considering alarming
        :return: true if gaitspeed trend is alarming, false if not
        """

        # detect trend
        if self.model is None:
            slope = self.normalize_and_fit()
        else:
            slope = self.model.estimator_.coef_

        # determine if trend is alarming
        if slope < threshold:
            return True
        else:
            return False
