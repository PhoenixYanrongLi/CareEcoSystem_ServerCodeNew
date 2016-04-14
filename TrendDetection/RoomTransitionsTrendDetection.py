__author__ = 'gmn255'

from TrendDetectionClass import TrendDetectionClass

class DailyRoomTransitionsTrendDetection(TrendDetectionClass):
    """
    This class detects alarming trends based on the daily roomtransitions data stream
    """

    def __init__(self, datalist):
        """
        constructor
        """
        super(DailyRoomTransitionsTrendDetection, self).__init__(datalist)

    def is_most_recent_trend_alarming(self, threshold=-0.0001):
        """
        Detect trends in most recent roomtransitions values
        :param threshold: value of slope below which trend should be considering alarming
        :return: true if roomtransitions trend is alarming, false if not
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
