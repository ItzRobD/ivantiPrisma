## Used AI to generate this generator for a quick randomized dataset

import random
import string

# template = {
#   "nextPageToken": {
#     "failedEventOffset": true,
#     "lastRowIdx": 0,
#     "limit": 0,
#     "offset": 0,
#     "previousTotalMatchedCount": 0,
#     "timestamp": 0
#   },
#   "pageSize": 0,
#   "resources": [
#     {
#       "accountId": "string",
#       "accountName": "string",
#       "alertStatus": {
#         "critical": 0,
#         "high": 0,
#         "informational": 0,
#         "low": 0,
#         "medium": 0
#       },
#       "appNames": [
#         "string"
#       ],
#       "assetType": "string",
#       "cloudType": "ALL",
#       "id": "string",
#       "name": "string",
#       "overallPassed": true,
#       "regionId": "string",
#       "regionName": "string",
#       "resourceConfigJsonAvailable": true,
#       "resourceDetailsAvailable": true,
#       "rrn": "string",
#       "scannedPolicies": [
#         {
#           "id": "string",
#           "labels": [
#             "string"
#           ],
#           "name": "string",
#           "passed": true,
#           "severity": "INFORMATIONAL"
#         }
#       ],
#       "unifiedAssetId": "string",
#       "vulnerabilityStatus": {
#         "critical": 0,
#         "high": 0,
#         "low": 0,
#         "medium": 0
#       }
#     }
#   ],
#   "timestamp": 0,
#   "totalMatchedCount": 0
# }

template = {
    "nextPageToken": {
        "failedEventOffset": True,
        "lastRowIdx": 0,
        "limit": 0,
        "offset": 0,
        "previousTotalMatchedCount": 0,
        "timestamp": 0
    },
    "pageSize": 0,
    "resources": [],
    "timestamp": 0,
    "totalMatchedCount": 0
}


def generate_random_string(length=10):
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=length))


def generate_random_number(max_value=10):
    return random.randint(0, max_value)


for _ in range(80):
    resource = {
        "accountId": generate_random_string(),
        "accountName": generate_random_string(),
        "alertStatus": {
            "critical": generate_random_number(),
            "high": generate_random_number(),
            "informational": generate_random_number(),
            "low": generate_random_number(),
            "medium": generate_random_number()
        },
        "appNames": [generate_random_string() for _ in range(random.randint(1, 3))],
        "assetType": "string",
        "cloudType": "ALL",
        "id": generate_random_string(),
        "name": generate_random_string(),
        "overallPassed": random.choice([True, False]),
        "regionId": generate_random_string(),
        "regionName": generate_random_string(),
        "resourceConfigJsonAvailable": True,
        "resourceDetailsAvailable": True,
        "rrn": generate_random_string(),
        "scannedPolicies": [
            {
                "id": generate_random_string(),
                "labels": [generate_random_string() for _ in range(random.randint(1, 3))],
                "name": generate_random_string(),
                "passed": random.choice([True, False]),
                "severity": random.choice(["INFORMATIONAL", "LOW", "MEDIUM", "HIGH", "CRITICAL"]),
            }
        ],
        "unifiedAssetId": generate_random_string(),
        "vulnerabilityStatus": {
            "critical": generate_random_number(),
            "high": generate_random_number(),
            "low": generate_random_number(),
            "medium": generate_random_number(),
        }
    }
    template['resources'].append(resource)

import json

with open('test_data.json', 'w') as f:
    json.dump(template, f, indent=4)