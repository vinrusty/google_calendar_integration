from django.shortcuts import redirect

# Create your views here.
from rest_framework.decorators import api_view
from rest_framework.response import Response

import google.oauth2.credentials
import google_auth_oauthlib.flow
import googleapiclient.discovery
import os
import json

os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'
CLIENT_SECRETS_ENV_VAR = 'GOOGLE_OAUTH_SECRET'

SCOPES = [
    'https://www.googleapis.com/auth/calendar',
    'https://www.googleapis.com/auth/userinfo.email',
    'https://www.googleapis.com/auth/userinfo.profile', 'openid'
]
# REDIRECT_URL = 'http://127.0.0.1:8000/rest/v1/calendar/redirect'
REDIRECT_URL = 'https://googlecalenderintegration.vineethhr.repl.co/rest/v1/calendar/redirect'
API_SERVICE_NAME = 'calendar'
API_VERSION = 'v3'


@api_view(['GET'])
def GoogleCalendarInitView(request):
    client_secrets_dict = json.loads(os.environ.get(CLIENT_SECRETS_ENV_VAR))

    flow = google_auth_oauthlib.flow.Flow.from_client_config(
        client_secrets_dict, scopes=SCOPES, redirect_uri=REDIRECT_URL)

    authorization_url, state = flow.authorization_url(
        access_type='offline', include_granted_scopes='true')

    request.session['state'] = state

    return redirect(authorization_url)


@api_view(['GET'])
def GoogleCalendarRedirectView(request):
    state = request.session['state']
    if state is None:
        return Response({"error": "State parameter missing."})

    client_secrets_dict = json.loads(os.environ.get(CLIENT_SECRETS_ENV_VAR))

    flow = google_auth_oauthlib.flow.Flow.from_client_config(
        client_secrets_dict, scopes=SCOPES, redirect_uri=REDIRECT_URL)

    authorization_response = request.get_full_path()
    flow.fetch_token(authorization_response=authorization_response)

    credentials = flow.credentials
    request.session['credentials'] = credentials_to_dict(credentials)

    if 'credentials' not in request.session:
        return redirect('v1/calendar/init')

    credentials = google.oauth2.credentials.Credentials(
        **request.session['credentials'])

    service = googleapiclient.discovery.build(API_SERVICE_NAME,
                                              API_VERSION,
                                              credentials=credentials,
                                              static_discovery=False)

    calendar_list = service.calendarList().list().execute()

    calendar_id = calendar_list['items'][0]['id']

    events = service.events().list(calendarId=calendar_id).execute()

    events_list_append = []
    if not events['items']:
        print('No data found.')
        return Response(
            {"message": "No data found or user credentials invalid."})
    else:
        for events_list in events['items']:
            events_list_append.append(events_list)

    return Response({"events": events_list_append})


def credentials_to_dict(credentials):
    return {
        'token': credentials.token,
        'refresh_token': credentials.refresh_token,
        'token_uri': credentials.token_uri,
        'client_id': credentials.client_id,
        'client_secret': credentials.client_secret,
        'scopes': credentials.scopes
    }
