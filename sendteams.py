import requests
import json
import logging

logging.basicConfig(filename='logs/saleforce.log', level=logging.INFO,
                    format='%(asctime)s %(levelname)s %(name)s %(message)s')
logger = logging.getLogger("teamslogger")


def sendtoteams(data):

    MSTEAMS_WEBHOOK = ("https://fountaintherapeutics.webhook.office.com/webhookb2/9809d5f8-9b5d-4b62-9c85-848c73a58fbe"
                       "@5750f6b7-444f-4867-bd33-64383f029011/IncomingWebhook/18b21424a727463288e420e8e8bf356c/5e224546"
                       "-b3e3-4309-9541-b11079123818")
    # Create your HTML table
    html_table = """
    <table style='margin-bottom: 30px;'>
      {{content}}
    </table>
    """
    teams_content = html_table.replace('{{content}}', data)
    # Create the message to send - you need to use markdown in Teams
    message = {
        "text": f"<h2>Salesforce Logins For Review:</h2><br><br>{teams_content}"
    }
    # POST the message to Microsoft Teams
    response = requests.post(MSTEAMS_WEBHOOK, headers={"Content-Type": "application/json"}, data=json.dumps(message))
    # Check for successful posting
    if response.status_code == 200:
        logger.info("Message sent successfully")
    else:
        logger.critical(f"Failed to send message: {response.status_code}, {response.text}")


