import os
import json
import logging
from time import sleep
import requests
from multiprocessing import Process
from ratelimit import limits, RateLimitException
from prometheus_client import start_http_server, Counter

log_dir = os.path.join(os.path.dirname(__file__), '../logs')
os.makedirs(log_dir, exist_ok=True)

logging.basicConfig(
    filename=os.path.join(log_dir, 'sms_log.log'),
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# Define metrics
sms_sent_counter = Counter('sms_sent', 'Number of SMS sent successfully')

# Start Prometheus HTTP server on port 8000
start_http_server(8000)

ONE_MINUTE = 60

def load_configuration():
    try:
        with open(r"C:/Users/vinay/PycharmProjects/SMS_Sending_System/configurations/config.json") as f:
            config = json.load(f)
            logging.info("Loaded configuration for country-operator pairs.")
            return config
    except FileNotFoundError:
        logging.error("Configuration file not found.")
        return {}
    except json.JSONDecodeError:
        logging.error("Error decoding JSON configuration.")
        return {}

class SendSMS:
    def __init__(self, country, operator, priority):
        self.phone_number = f"+{self.generate_phone_number(country)}"
        self.proxy = f"{operator}_proxy"
        self.priority = priority

    def generate_phone_number(self, country):
        country_prefixes = {
            "Uzbekistan": "998",
            "India": "91",
            "Ukraine": "380",
            "Tajikistan": "992"
        }
        prefix = country_prefixes.get(country, "000")
        return f"{prefix}123456789"

    def send_otp(self):
        print(f"Sending OTP to {self.phone_number} using proxy {self.proxy} (Priority: {self.priority})")
        response = "sent successfully"
        return 'sent successfully' in response

class SubmitSMS:
    def submit_otp(self, trigger_id, sms_code):
        print(f"Submitting OTP {sms_code} for trigger ID {trigger_id}")
        response = "submitted successfully"
        return 'submitted successfully' in response

@limits(calls=10, period=ONE_MINUTE)
def send_sms_rate_limited(country, operator, priority):
    try:
        sms = SendSMS(country, operator, priority)
        success = sms.send_otp()
        print(f"OTP sent to {sms.phone_number}: {'Success' if success else 'Failed'}")
        return success
    except RateLimitException:
        print("Rate limit exceeded. Waiting before retrying...")
        sleep(ONE_MINUTE)
        return send_sms_rate_limited(country, operator, priority)

def start_sms_process(country, operator, priority):
    try:
        success = send_sms_rate_limited(country, operator, priority)
        if success:
            logging.info(f"SMS sent successfully to {country} ({operator})")
            sms_sent_counter.inc()  
            print("Counter incremented") 
        else:
            logging.error(f"Failed to send SMS to {country} ({operator})")
    except Exception as e:
        logging.error(f"Error in start_sms_process for {country}, {operator}: {e}")

if __name__ == "__main__":
    config = load_configuration()
    country_operator_pairs = config.get("country_operator_pairs", [])
    
    try:
        while True:
            processes = []
            for pair in country_operator_pairs:
                country = pair.get("country")
                operator = pair.get("operator")
                priority = pair.get("priority", False)
                p = Process(target=start_sms_process, args=(country, operator, priority))
                p.start()
                processes.append(p)

            for p in processes:
                p.join()

            sleep(10)
    except KeyboardInterrupt:
        print("Shutting down gracefully...")
        logging.info("Shutting down gracefully due to KeyboardInterrupt")
