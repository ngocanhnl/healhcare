import os
from datetime import timedelta

from dotenv import load_dotenv

load_dotenv()


class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key-change-me")

    # MySQL example:
    # mysql+pymysql://user:password@localhost:3306/medical_platform?charset=utf8mb4
    SQLALCHEMY_DATABASE_URI = os.getenv(
        "DATABASE_URL",
        "mysql+pymysql://root:root@localhost:3307/medical_platform?charset=utf8mb4",
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    REMEMBER_COOKIE_DURATION = timedelta(days=7)
    SESSION_COOKIE_HTTPONLY = True
    WTF_CSRF_TIME_LIMIT = None

    # VNPay configuration
    VNPAY_VERSION = os.getenv("VNPAY_VERSION", "2.1.0")
    VNPAY_TMN_CODE = os.getenv("VNPAY_TMN_CODE", "ODZ5NOX0")
    VNPAY_HASH_SECRET = os.getenv("VNPAY_HASH_SECRET", "5V52YZPPD3EHTSGJOQQ9XG6VIREUZQLG")
    VNPAY_PAYMENT_URL = os.getenv(
        "VNPAY_PAYMENT_URL",
        "https://sandbox.vnpayment.vn/paymentv2/vpcpay.html",
    )
    VNPAY_RETURN_URL_PATH = os.getenv("VNPAY_RETURN_URL_PATH", "/vnpay/return")
    VNPAY_LOCALE = os.getenv("VNPAY_LOCALE", "vn")
    VNPAY_CURR_CODE = os.getenv("VNPAY_CURR_CODE", "VND")
    VNPAY_ORDER_TYPE = os.getenv("VNPAY_ORDER_TYPE", "other")

