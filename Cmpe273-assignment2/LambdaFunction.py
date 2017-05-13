from __future__ import print_function
from datetime import datetime
from botocore.exceptions import ClientError
from boto3.dynamodb.conditions import Key, Attr

import boto3
import json

def respond(err, message=None):
    if err:
        return {
            'statusCode': err
        }
    else:
        return {
            'message': message
        }

def lambda_handler(event, context):

    operations = {
        #'DELETE': lambda dynamo, x: dynamo.delete_item(**x),
        'GET': lambda dynamo, x: dynamo.scan(**x),
        'POST': lambda dynamo, x: dynamo.put_item(**x),
        'PUT': lambda dynamo, x: dynamo.update_item(**x),
    }

    operation = event['httpMethod']
    if operation in operations:
        dynamo = boto3.resource('dynamodb')
        menuTable = dynamo.Table('PizzaMenu')
        orderTable = dynamo.Table(event['TableName'])
        
        # Post operation #
        if operation == 'POST':
            payload = event['body']
            response = operations[operation](orderTable, payload)
            try:
                response = menuTable.get_item(
                    Key={
                        'menu_id': event['body']['Item']['menu_id']
                    }
                )
            except ClientError as e:
                return e.response['Error']['Message']
            else:
                if response['ResponseMetadata']['HTTPStatusCode'] != 200:
                    return respond(response['ResponseMetadata']['HTTPStatusCode'], None)
                temp = response['Item']
                mystr = ""
                lim = ""
                for idx, item in enumerate(temp['selection']):
                    mystr = mystr+lim+str(idx+1)+". "+item
                    lim = ", "
                mystr = "Hello %s, please choose one of these selection: " % event['body']['Item']['customer_name'] + mystr
                return respond(None, mystr) 
            
        elif operation == 'PUT':
            user_input = int(event['input'])
            try:
                orderResp = orderTable.get_item(
                    Key={
                        'order_id': event['order_id']
                    }
                )
            except ClientError as e:
                return e.response['Error']['Message']
            else:
                temp = orderResp['Item']
                try:
                    menuResp = menuTable.get_item(
                        Key={
                            'menu_id': temp['menu_id']
                        }
                    )
                except ClientError as e:
                    return e.response['Error']['Message']
                else:
                    temp1 = menuResp['Item']
                    if 'order_status' in temp.keys():
                        order_status = temp['order_status']
                        if order_status == 'size':
                            if(user_input > len(temp1['size'])):
                                return respond(None, "Invalid Option for Size!")
                            order = temp['order']
                            response = orderTable.update_item(
                                Key={
                                    'order_id': event['order_id']
                                },
                                UpdateExpression="set order_status = :r, #ord = :v",
                                ExpressionAttributeNames={
                                    "#ord": "order"    
                                },
                                ExpressionAttributeValues={
                                    ':r': "processing",
                                    ':v': { 
                                        "selection": order['selection'],
                                        "size": temp1['size'][user_input-1],
                                        "costs": temp1['price'][user_input-1],
                                        "order_time": datetime.now().strftime('%m-%d-%Y@%H:%M:%S')
                                    }
                                }
                            )
                            if response['ResponseMetadata']['HTTPStatusCode'] != 200:
                                return respond(response['ResponseMetadata']['HTTPStatusCode'], None)
                            mystr = "Your order costs %s. We will email you when the order is ready. Thank you!" % temp1['price'][user_input-1]
                            return respond(None, mystr)
                        elif order_status == 'processing':
                            return respond(None, "Your order is being processed. Please wait for our email!")
                        else:
                            return respond(None, "Error: Order Status invalid!")
                       
                    else:
                        if(user_input > len(temp1['selection'])):
                            return respond(None, "Invalid Selection!")
                        
                        response = orderTable.update_item(
                            Key={
                                'order_id': event['order_id']
                            },
                            UpdateExpression="set order_status = :r, #ord = :v",
                            ExpressionAttributeNames={
                                "#ord": "order"    
                            },
                            ExpressionAttributeValues={
                                ':r': "size",
                                ':v': { 
                                        "selection": temp1['selection'][user_input-1]
                                    }
                            }
                        )
                        if response['ResponseMetadata']['HTTPStatusCode'] != 200:
                            return respond(response['ResponseMetadata']['HTTPStatusCode'], None)
                        mystr = ""
                        lim = ""
                        for idx, item in enumerate(temp1['size']):
                            mystr = mystr+lim+str(idx+1)+". "+item
                            lim = ", "
                        mystr = "Which size do you want? " + mystr
                        return respond(None, mystr)
                        
        elif operation == 'GET':                    
            response = orderTable.query(
                KeyConditionExpression=Key('order_id').eq(event['order_id'])
            )
            if response['ResponseMetadata']['HTTPStatusCode'] == 200:
                if 'Items' in response.keys() and len(response['Items']) > 0:
                    return response['Items'][0]
                else:
                    return respond(None, "%s not found!" % event['order_id'])
            else:
                return respond(None, "Error retrieving data!")
    else:
        return respond(None, "Unknown Operation: %s" % operation)

