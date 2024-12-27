from flask import Flask, render_template, request, jsonify
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service
from pymongo import MongoClient
from datetime import datetime
from selenium.webdriver.support.ui import WebDriverWait
import uuid
from selenium.webdriver.support import expected_conditions as EC
import requests
import os

app = Flask(__name__)

mongo_uri = os.getenv("MONGO_URI")
# MongoDB setup
client = MongoClient(mongo_uri)
db = client["twitter_trends"]
collection = db["trends"]

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/run-script', methods=['POST'])
def run_script():
    try:
        # Selenium setup
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service)
        
        # Log in to Twitter
        driver.get("https://x.com/login")
        username = WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "input[name='text']"))
        )
        username.send_keys("rizznikant")  # Replace with your Twitter username/email
        username.send_keys(Keys.RETURN)

        password = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.NAME, "password"))
        )
        password.send_keys("rajnikisajni892@")  # Replace with your Twitter password
        password.send_keys(Keys.RETURN)

        # Wait for successful login
        WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "a[href='/home']"))
        )
        print("Successfully logged in!")

        # Navigate to the home page
        driver.get("https://x.com/home")
        print("Reached home page.")

        trends = []
        while len(trends) < 5:
            try:
                # Fetch currently visible trends
                visible_trends = WebDriverWait(driver, 10).until(
                    EC.presence_of_all_elements_located((By.CSS_SELECTOR, "[data-testid='trend']"))
                )
                print(f"Found {len(visible_trends)} trends.")
                for trend in visible_trends:
                    if len(trends) < 5:
                        trend_text = trend.text.strip() if trend.text else "No Content"
                        if trend_text not in trends:
                            trends.append(trend_text)
                            print(f"Added trend: {trend_text}")
                    else:
                        break

                # Check for 'Show More' button
                try:
                    show_more_button = WebDriverWait(driver, 10).until(
                        EC.element_to_be_clickable((By.XPATH, "//a[contains(@href, '/explore/tabs/for-you')]"))
                    )
                    print("Clicking 'Show More' button...")
                    show_more_button.click()
                    WebDriverWait(driver, 10).until(EC.staleness_of(visible_trends[0]))
                except Exception as e:
                    print("No 'Show More' button found or error:", e)
                    break
            except Exception as e:
                print(f"Error while loading trends: {e}")
                # Capture and log page source for debugging
                break

        # Fill missing trends with N/A if fewer than 5 are collected
        while len(trends) < 5:
            trends.append("N/A")

        # Save to MongoDB
        unique_id = str(uuid.uuid4())
        ip_address = requests.get('https://api64.ipify.org?format=json').json()['ip']
        end_time = datetime.now()

        data = {
            "_id": unique_id,
            "name_of_trend1": trends[0],
            "name_of_trend2": trends[1],
            "name_of_trend3": trends[2],
            "name_of_trend4": trends[3],
            "name_of_trend5": trends[4],
            "date_time": end_time,
            "ip_address": ip_address
        }
        collection.insert_one(data)

        # Return response
        response = {
            "trends": trends,
            "timestamp": end_time.strftime("%Y-%m-%d %H:%M:%S"),
            "ip_address": ip_address
        }
        return jsonify(response)

    except Exception as e:
        return jsonify({"error": str(e)})

    finally:
        driver.quit()


if __name__ == "__main__":
    app.run(debug=True)
