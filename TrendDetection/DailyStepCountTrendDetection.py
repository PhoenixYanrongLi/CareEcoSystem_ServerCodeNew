__author__ = 'gmn255'

from TrendDetectionClass import TrendDetectionClass


class DailyStepCountTrendDetection(TrendDetectionClass):
    """
    This class detects alarming trends based on the daily step count data stream
    """ 

    def __init__(self, datalist):
        """
        constructor
        """
        super(DailyStepCountTrendDetection, self).__init__(datalist)

    def is_most_recent_trend_alarming(self, threshold=-0.00033):
        """
        Detect trends in most recent stepcount values
        :param threshold: value of slope below which trend should be considering alarming
        :return: true if stepcount trend is alarming, false if not
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



