__author__ = 'Brad'
from simple_salesforce import Salesforce
import json
sf = Salesforce( username='fm-integration@careeco.uat', password='fmr0cks!', security_token='vnWYJMNtLbDPL9NY97JP9tJ5', sandbox=True)
print sf

metricData ={
    "patientId": "DCE-2762",
    "timestamp": "6/11/2015 12:00 AM",

    "roomPercentages": [
        {
            "room": "Bathroom",
            "percentage": 100
        },
        {
            "room": "Livingroom",
            "percentage": 100
        },
        {
            "room": "Kitchen",
            "percentage": 100
        }
    ]
}
print metricData
result = sf.apexecute('FMMetrics/insertMetrics', method='POST', data=metricData)
print result