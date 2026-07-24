# from app import create_app: Imports the function to create an instance of the Flask app.
from app import create_app
# from app.models import db: Imports the db instance from models to manage the database.
from app.models import db, Customer
from app.utils.util import encode_token
# import unittest: Imports Python’s unittest framework for setting up and running tests.
import unittest

# TestMember Class: Defines a test class inheriting from unittest.TestCase.
class TestCustomer(unittest.TestCase):
    # setUp Method: 
    def setUp(self):
        # Creates a test app instance using TestingConfig.
        self.app = create_app("TestingConfig")
        self.customer = Customer(name="test_user", email="test@email.com", phone="1111111111" , password='test')
        # Initializes a test database context:
        with self.app.app_context():
            # db.drop_all(): Clears existing tables to reset the database.
            db.drop_all()
            # db.create_all(): Sets up fresh tables for each test.
            db.create_all()
            db.session.add(self.customer)
            db.session.commit()
            
            self.customer_id = self.customer.id
            
        self.token = encode_token(self.customer_id)
        # Sets up a test client to simulate requests.
        self.client = self.app.test_client()

    # CREATE CUSTOMER ACCOUNT TESTS    
    def test_create_customer(self):
        # customer_payload: Defines the data for a new customer.
        customer_payload = {
            "name": "John Doe",
            "email": "jd@email.com",
            "phone": "1234567890",
            "password": "1234"
        }
        
        # Send POST Request:
        # Sends a POST request to the /customers/ endpoint with customer_payload as JSON data.
        # Note you must send the request to the endpoint with a trailing '/' (i.e. /customers/) on any endpoint consisting of JUST the url_prefix for the blueprint.
        response = self.client.post('/customers/', json=customer_payload)
        # Assertions:
        # Verifies that the response status code is 201 (Created).
        self.assertEqual(response.status_code, 201)
        # Checks that the returned JSON contains the expected customer name.
        self.assertEqual(response.json['name'], "John Doe")
        self.assertNotIn("password", response.json)
        
    def test_invalid_creation(self):
        # Set up an incomplete customer payload without the required email field.
        customer_payload = {
            "name": "John Doe",
            "phone": "123-456-7890",
            "password": "123"       
        }

        # Attempt to create a customer with the incomplete payload.
        response = self.client.post('/customers/', json=customer_payload)
        # Assertions:
        # Ensures that the API returns a 400 status code, indicating a bad request due to the missing field:
        self.assertEqual(response.status_code, 400)
        # Verifies that the response message specifies the missing email field:
        self.assertEqual(response.json['email'], ['Missing data for required field.'])
    
    # LOGIN TESTS    
    def test_login_customer(self):
        credentials = {
            "email": "test@email.com",
            "password": "test"
        }
        
        response = self.client.post('/customers/login', json=credentials)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json['status'], 'success')
        self.assertIn("auth_token", response.json)
    
    def test_invalid_login(self):
        credentials = {
            "email": "bad_email@email.com",
            "password": "bad_pw"
        }

        response = self.client.post('/customers/login', json=credentials)
        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.json['message'], 'Invalid email or password')
    
    # UPDATE TESTS    
    def test_update_customer(self):
        update_payload = {
            "name": "Peter",
            "email": "test@email.com",
            "phone": "1111111111",           
            "password": "test"
        }

        headers = {'Authorization': f"Bearer {self.token}"}

        response = self.client.put('/customers/', json=update_payload, headers=headers)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json['name'], 'Peter') 
        self.assertEqual(response.json['email'], 'test@email.com')

        with self.app.app_context():
            updated_customer = db.session.get(Customer, self.customer_id)
            self.assertEqual(updated_customer.name, "Peter")
            self.assertEqual(updated_customer.email, "test@email.com")

    # GET CUSTOMERS TEST    
    def test_get_customers(self):
        response = self.client.get('/customers/')
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json), 1)
        self.assertEqual(
            response.json[0]["email"],
            "test@email.com"
        )
        
    # GET SPECIFIC CUSTOMER TEST    
    def test_get_customer(self):
        response = self.client.get(f"/customers/{self.customer_id}")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json["id"], self.customer_id)
        self.assertEqual(response.json["email"], "test@email.com")
                
    # DELETE CUSTOMER TEST    
    def test_delete_customer(self):

        headers = {'Authorization': f"Bearer {self.token}"}

        response = self.client.delete('/customers/', headers=headers)
        
        self.assertEqual(response.status_code, 200)
        self.assertIn("successfully deleted", response.json["message"])

        with self.app.app_context():
            deleted_customer = db.session.get(
                Customer,
                self.customer_id
            )
            self.assertIsNone(deleted_customer)
        
# run in terminal: python -m unittest discover tests
