import smtplib

EMAIL = "bangjame2004@gmail.com"
PASSWORD = "roujmlzhstvzwvll"

try:
    smtp = smtplib.SMTP("smtp.gmail.com", 587)
    smtp.ehlo()
    smtp.starttls()
    smtp.ehlo()

    smtp.login(EMAIL, PASSWORD)

    print("LOGIN SUCCESS")

except Exception as e:
    print(e)