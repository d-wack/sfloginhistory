#!/home/ubuntu/.pyenv/shims/python
from simple_salesforce import Salesforce, SalesforceAuthenticationFailed, SalesforceGeneralError
from datetime import datetime, timedelta, timezone
from botocore.exceptions import ClientError
import boto3
import argparse
import os
import json
import logging

parser = argparse.ArgumentParser(description="Allows Setting internal variables")
parser.add_argument("days", type=int, nargs='?', help="Specify number of days to pull", default=1)
parser.add_argument("--dev", action="store_true", help="Sets Dev to Tru")
args = parser.parse_args()

DEV = True if args.dev else False
DAYS_OF_LOGS_TO_PULL = args.days

logging.basicConfig(filename='logs/saleforce.log', level=logging.INFO,
                    format='%(asctime)s %(levelname)s %(name)s %(message)s')
logger = logging.getLogger("logger")


def get_secret():
    secret_name = "prod/salesforce_event_api"
    region_name = "us-east-1"

    # Create a Secrets Manager client
    session = boto3.session.Session()
    client = session.client(
        service_name='secretsmanager',
        region_name=region_name
    )

    try:
        get_secret_value_response = client.get_secret_value(
            SecretId=secret_name
        )
    except ClientError as e:
        # For a list of exceptions thrown, see
        # https://docs.aws.amazon.com/secretsmanager/latest/apireference/API_GetSecretValue.html
        raise e

    # Decrypts secret using the associated KMS key

    return json.loads(get_secret_value_response['SecretString'])


def get_username(sf, user_id):
    results = sf.query_all_iter(
        "SELECT Username FROM User WHERE Id='{0}'".format(user_id))
    for result in results:
        return result.get('Username')


def get_last_login_time(organization):
    filename = f'{organization}_sf_login_history.log'
    if os.path.isfile(filename):
        with open(filename, 'r', newline="\n") as log:
            lines = log.readlines()[-1]
            return json.loads(lines)["LoginTime"]
    else:
        return (datetime.now(timezone.utc) - timedelta(days=DAYS_OF_LOGS_TO_PULL)).strftime('%Y-%m-%dT%H:%M:%S.%f%z')


def get_sf_logs(organization, credentials):
    sf = None
    if organization == 'fountainlife':
        logger.info("Pulling Fountainlife Salesforce Login History Logs")
        try:
            sf = Salesforce(username=credentials["FL_USERNAME"], password=credentials["PASSWORD"],
                            security_token=credentials["FL_TOKEN"])
            logger.info("Successfully Authenticated with Fountainlife Salesforce")
        except SalesforceAuthenticationFailed:
            logger.critical("Authentication Failed - Fountainlife")
            exit()
        except SalesforceGeneralError as e:
            logger.error(e.message)
    else:
        logger.info("Pulling FountainHealth Salesforce Login History Logs")
        try:
            sf = Salesforce(username=credentials["FH_USERNAME"], password=credentials["PASSWORD"],
                            security_token=credentials["FH_TOKEN"])
            logger.info("Successfully Authenticated with FountainHealth Salesforce")
        except SalesforceAuthenticationFailed:
            logger.critical("Authentication Failed - FountainHealth")
            exit()
        except SalesforceGeneralError as e:
            logger.error(e.message)
    if DEV:
        print(type(get_last_login_time(organization=org)))
        print(get_last_login_time(organization=org))

    query = (f"SELECT\n"
             f"LoginTime,UserID,Status,SourceIP,Platform,Application,\n"
             f"LoginGeoId,CountryIso\n"
             f"FROM LoginHistory\n"
             f"WHERE LoginType != 'Remote Access 2.0' AND\n"
             f"LoginTime > {get_last_login_time(organization=org)}\n"
             f"ORDER BY LoginTime ASC\n"
             f"")
    results = sf.query(query=query)
    if len(results.get('records')) > 0:
        for result in results.get('records'):
            if result.get('LoginGeoId') is not None:
                locations = sf.query(
                    f"SELECT Country,City, Latitude, Longitude FROM LoginGeo WHERE Id='{result.get('LoginGeoId')}'")
                records = locations.get('records')[0]
                latitude = records.get('Latitude')
                longitude = records.get('Longitude')
                city = records.get('City')
            else:
                latitude = None
                longitude = None
                city = None
            login = {
                "LoginTime": datetime.strptime(result.get('LoginTime'), '%Y-%m-%dT%H:%M:%S.%f%z').isoformat(),
                "LoginType": result.get('LoginType'),
                "Username": get_username(sf=sf, user_id=result.get('UserId')),
                "Location": {"Longitude": longitude, "Latitude": latitude, "City": city,
                             "Country": result.get('CountryIso')},
                "Status": result.get('Status'),
                "LoginUrl": result.get('LoginUrl'),
                "Application": result.get('Application'),
                "Platform": result.get('Platform'),
                "Organization": organization
            }
            if DEV:
                print(login)
            with open("{}.log".format(organization), "a", encoding='utf-8') as logs:
                logs.write(json.dumps(login) + '\n')
    else:
        logger.info("No records found!!")


orgs = ['fountainlife', 'fountainhealth']
creds = get_secret()
for org in orgs:
    get_sf_logs(organization=org, credentials=creds)
