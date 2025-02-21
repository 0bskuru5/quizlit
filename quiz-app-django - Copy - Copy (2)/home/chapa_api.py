import requests
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from .models import Payment

try:
    SECRET = settings.CHAPA_SECRET
    API_URL = settings.CHAPA_API_URL
    API_VERSION = settings.CHAPA_API_VERSION
    CALLBACK_URL = settings.CHAPA_CALLBACK_URL
    CHAPA_RETURN_URL = settings.CHAPA_RETURN_URL    
except AttributeError as e:
    raise ImproperlyConfigured(f"One or more Chapa config missing: {e}, please check your settings file")

class ChapaAPI:
    @classmethod
    def get_headers(cls) -> dict:
        """Return the headers with the API key."""
        return {
            'Content-type': 'application/json',
            'Authorization': f'Bearer {SECRET}'
        }

    @classmethod
    def get_base_url(cls) -> str:
        """Return the base API URL."""
        return f"{API_URL}/{API_VERSION}"

    @classmethod
    def initialize_payment(cls, payment: Payment, update_record=True) -> dict:
        """Send payment initialization request."""
        data = {
            'amount': float(payment.amount),
            'currency': 'ETB',  # Adjust currency if needed
            'email': payment.user.email,
            'first_name': payment.user.first_name,
            'last_name': payment.user.last_name,
            'tx_ref': str(payment.id),
            'callback_url': CALLBACK_URL,
            'return_url': CHAPA_RETURN_URL,
            'customization[title]': f"Quiz Payment: {payment.quiz.category.name}",
            'customization[description]': f"Payment for {payment.quiz.category.name} quiz",
            'phone_number': payment.user.profile.phone_number if hasattr(payment.user, 'profile') else ''
        }

        transaction_url = f'{cls.get_base_url()}/transaction/initialize'
        response = requests.post(transaction_url, json=data, headers=cls.get_headers())
        print(f"Response from Chapa API: {response.json()}")  # Debugging
        data = response.json()

        if data and data.get('status') == 'success' and update_record:
            payment.status = 'pending'
            payment.payment_reference = data['data'].get('tx_ref')
            payment.save()

        return data

    @classmethod
    def verify_payment(cls, payment: Payment) -> dict:
        """Verify the payment status using the transaction ID."""
        url = f'{cls.get_base_url()}/transaction/verify/{payment.payment_reference}'
        response = requests.get(url, headers=cls.get_headers())
        return response.json()
