from pyfcm import FCMNotification
from django.conf import settings
import threading

def push_notification(fcm_token, message_title, message_body, payload):
    '''
    The code starts by creating a new FCMNotification object.
    The API_KEY is the key that was set in the settings file, and it's used to identify this notification as belonging to your app.
    Next, the push_service is created with an api_key of settings.API_KEY .
    This service will be used for sending out notifications to multiple devices at once.
    The notify method on the push service sends out a message with data about what happened (the title and body) to all registered devices using their token IDs from registration ids=[fcm_token] .
    The code is to push a notification to multiple devices.
    The code above pushes the notification to all registered devices with the given FCM token.
    '''
    push_service = FCMNotification(api_key=settings.FIREBASE_SERVER_KEY)
    push_service.notify_multiple_devices(registration_ids=[fcm_token], message_title=message_title, message_body=message_body, data_message=payload)
