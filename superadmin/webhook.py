from django.views.decorators.csrf import csrf_exempt
from .utils import *
from django.http import HttpResponse, JsonResponse


@csrf_exempt
def TestSubscriptionCompletedwebhook(request):
    endpoint_secret = settings.STRIPE_ENDPOINT_SECRET
    event = None
    payload = request.body
    sig_header = request.headers['STRIPE_SIGNATURE']
    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, endpoint_secret
        )
    except ValueError as e:
        # Invalid payload
        raise e
    except stripe.error.SignatureVerificationError as e:
        # Invalid signature
        raise e

    # Handle the event
    if event['type'] == 'invoice.paid':
        subscription_schedule = event['data']['object']
        print(subscription_schedule, '----------')
    else:
      print('Unhandled event type {}'.format(event['type']))

    return JsonResponse({
        'success':True
    })
