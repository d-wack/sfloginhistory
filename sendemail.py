import msal
import requests
import logging
from sendteams import sendtoteams
import os

basepath = os.path.dirname(os.path.realpath(__file__))
logfolder = os.path.join(basepath, 'logs')
logfile = os.path.join(logfolder, 'saleforce.log')

logging.basicConfig(filename=logfile, level=logging.INFO,
                    format='%(asctime)s %(levelname)s %(name)s %(message)s')
logger = logging.getLogger("maillogger")

DEV = True


def generate_html_table(data):
    table_html = (
        f"<tr><th style='background-color: cornflowerblue; color: white;'>Organization</th>"
        f"<th style='background-color: cornflowerblue; color: white;'>LoginTime</th>"
        f"<th style='background-color: cornflowerblue; color: white;'>Username</th>"
        f"<th style='background-color: cornflowerblue; color: white;'>City</th>"
        f"<th style='background-color: cornflowerblue; color: white;'>Country</th>"
        f"<th style='background-color: cornflowerblue; color: white;'>Status</th></tr>")
    for row in data:
        country_color = "#f70515" if row['Location']['Country'] != "US" else "#ffffff"
        status_color = "#f70515" if row['Status'] != "Success" else "#ffffff"
        table_html += (
            f"<tr><td>{row['Organization'].capitalize()}</td>"
            f"<td>{str(row['LoginTime']).replace('T', ' ').split('+')[0]}</td>"
            f"<td>{row['Username']}</td><td>{row['Location']['City']}</td>"
            f"<td style='background-color: {country_color};'>{row['Location']['Country']}</td>"
            f"<td style='background-color: {status_color};'>{row['Status']}</td></tr>")
        if DEV:
            print(table_html)
    return table_html


def send_alert(credentials, logins):
    with open(os.path.join(basepath, 'alerts_template.html'), 'r') as file:
        email_template = file.read()

    dynamic_table = generate_html_table(logins)
    sendtoteams(data=dynamic_table)
    email_content = email_template.replace('{{content}}', dynamic_table)

    client_id = credentials["MS365_CLIENT_ID"]
    client_secret = credentials["MS365_SECRET_ID"]
    tenant_id = credentials["MS365_TENANT_ID"]
    authority = f"https://login.microsoftonline.com/{tenant_id}"
    app = msal.ConfidentialClientApplication(
        client_id=client_id,
        client_credential=client_secret,
        authority=authority)
    scopes = ["https://graph.microsoft.com/.default"]
    result = app.acquire_token_silent(scopes, account=None)
    if not result:
        logger.info(
            "No suitable token exists in cache. Let's get a new one from Azure Active Directory.")
        result = app.acquire_token_for_client(scopes=scopes)
    if "access_token" in result:
        userId = credentials["MS365_USER_ID"]
        endpoint = f'https://graph.microsoft.com/v1.0/users/{userId}/sendMail'
        toUserEmail = "brandon.bailey@initres.com"
        email_msg = {'Message': {'Subject': "Test Sending Email from Python",
                                 'Body': {'ContentType': 'HTML', 'Content': f'{email_content}'},
                                 'ToRecipients': [{'EmailAddress': {'Address': toUserEmail}}]
                                 },
                     'SaveToSentItems': 'true'}
        r = requests.post(endpoint,
                          headers={'Authorization': 'Bearer ' + result['access_token']}, json=email_msg)
        if r.ok:
            logger.info('Sent email successfully')
        else:
            logger.info(r.json())
    else:
        logger.critical(result.get("error"))
        logger.critical(result.get("error_description"))
        logger.critical(result.get("correlation_id"))
