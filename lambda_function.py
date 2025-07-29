import json
from scrape_data import initiate_driver
def lambda_handler(event, context):
    # TODO implement
    initiate_driver()
    print('Done')
    return {
        'statusCode': 200,
        'body': json.dumps('Hello from Lambda!')
    }
