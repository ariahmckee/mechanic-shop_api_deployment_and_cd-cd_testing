from app import create_app
from app.models import Customer, db, Mechanic, Ticket
from app.utils.util import encode_mechanic_token
from datetime import date
import unittest

class TestMechanic(unittest.TestCase):
    def setUp(self):
        self.app = create_app("TestingConfig")
        self.mechanic = Mechanic(
            name="test_user",
            email="test@email.com",
            phone="1111111111",
            password="test",
            salary=60000
        )
        with self.app.app_context():
            db.drop_all()
            db.create_all()
            db.session.add(self.mechanic)
            db.session.commit()
            
            self.mechanic_id = self.mechanic.id
            
        self.token = encode_mechanic_token(self.mechanic_id)
        self.client = self.app.test_client()
    

    # CREATE MECHANIC ACCOUNT TESTS    
    def test_create_mechanic(self):
        mechanic_payload = {
            "name": "John Doe",
            "email": "jd@email.com",
            "phone": "1234567890",
            "password": "1234",
            "salary": 55000
        }
        
        response = self.client.post('/mechanics/', json=mechanic_payload)

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json['name'], "John Doe")
        self.assertNotIn("password", response.json)
        
    def test_invalid_creation(self):
        mechanic_payload = {
            "name": "John Doe",
            "phone": "123-456-7890",
            "password": "123",
            "salary": 55000
        }

        response = self.client.post('/mechanics/', json=mechanic_payload)

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json['email'], ['Missing data for required field.'])
    
    # LOGIN TESTS    
    def test_login_mechanic(self):
        credentials = {
            "email": "test@email.com",
            "password": "test"
        }
        
        response = self.client.post('/mechanics/login', json=credentials)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json['status'], 'success')
        self.assertIn("auth_token", response.json)
    
    def test_invalid_login(self):
        credentials = {
            "email": "bad_email@email.com",
            "password": "bad_pw"
        }

        response = self.client.post('/mechanics/login', json=credentials)
        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.json['message'], 'Invalid email or password')
    
    # UPDATE TESTS    
    def test_update_mechanic(self):
        update_payload = {
            "name": "Peter",
            "email": "test@email.com",
            "phone": "1111111111",           
            "password": "test",
            "salary": 65000
        }

        headers = {'Authorization': f"Bearer {self.token}"}

        response = self.client.put(
            f'/mechanics/{self.mechanic_id}',
            json=update_payload,
            headers=headers
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json['name'], 'Peter') 
        self.assertEqual(response.json['email'], 'test@email.com')

        with self.app.app_context():
            updated_mechanic = db.session.get(Mechanic, self.mechanic_id)
            self.assertEqual(updated_mechanic.name, "Peter")
            self.assertEqual(updated_mechanic.salary, 65000)

    def test_update_other_mechanic(self):
        other_mechanic = Mechanic(
            name="Other Mechanic",
            email="other@email.com",
            phone="2222222222",
            password="other-test",
            salary=50000
        )

        with self.app.app_context():
            db.session.add(other_mechanic)
            db.session.commit()
            other_mechanic_id = other_mechanic.id

        update_payload = {
            "name": "Unauthorized Update",
            "email": "other@email.com",
            "phone": "2222222222",
            "password": "other-test",
            "salary": 70000
        }
        headers = {"Authorization": f"Bearer {self.token}"}

        response = self.client.put(
            f"/mechanics/{other_mechanic_id}",
            json=update_payload,
            headers=headers
        )

        self.assertEqual(response.status_code, 403)
        self.assertEqual(
            response.json["error"],
            "You can only update your own mechanic profile."
        )

        with self.app.app_context():
            unchanged_mechanic = db.session.get(Mechanic, other_mechanic_id)
            self.assertEqual(unchanged_mechanic.name, "Other Mechanic")

    # GET MECHANICS TEST    
    def test_get_mechanics(self):
        response = self.client.get('/mechanics/')
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json), 1)
        self.assertEqual(
            response.json[0]["email"],
            "test@email.com"
        )
        
    # GET SPECIFIC MECHANIC TEST    
    def test_get_mechanic(self):
        response = self.client.get(f"/mechanics/{self.mechanic_id}")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json["id"], self.mechanic_id)
        self.assertEqual(response.json["email"], "test@email.com")

    # GET MECHANICS SORTED BY EXPERIENCE TEST
    def test_experienced_mechanics(self):
        experienced_mechanic = Mechanic(
            name="Experienced Mechanic",
            email="experienced@email.com",
            phone="2222222222",
            password="test",
            salary=75000
        )
        customer = Customer(
            name="Test Customer",
            email="customer@email.com",
            phone="3333333333",
            password="test"
        )

        with self.app.app_context():
            db.session.add_all([experienced_mechanic, customer])
            db.session.flush()

            first_ticket = Ticket(
                vin="TESTVIN000000001",
                ticket_date=date(2026, 7, 22),
                ticket_desc="First repair",
                customer_id=customer.id
            )
            second_ticket = Ticket(
                vin="TESTVIN000000002",
                ticket_date=date(2026, 7, 23),
                ticket_desc="Second repair",
                customer_id=customer.id
            )
            first_ticket.mechanics.append(experienced_mechanic)
            second_ticket.mechanics.append(experienced_mechanic)
            db.session.add_all([first_ticket, second_ticket])
            db.session.commit()
            experienced_mechanic_id = experienced_mechanic.id

        response = self.client.get("/mechanics/experience")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json[0]["id"], experienced_mechanic_id)
        self.assertEqual(response.json[0]["name"], "Experienced Mechanic")

    # SEARCH MECHANICS BY NAME TEST
    def test_search_mechanic(self):
        searchable_mechanic = Mechanic(
            name="Alice Wrench",
            email="alice@email.com",
            phone="4444444444",
            password="test",
            salary=62000
        )

        with self.app.app_context():
            db.session.add(searchable_mechanic)
            db.session.commit()
            searchable_mechanic_id = searchable_mechanic.id

        response = self.client.get("/mechanics/search?name=Alice")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json), 1)
        self.assertEqual(response.json[0]["id"], searchable_mechanic_id)
        self.assertEqual(response.json[0]["name"], "Alice Wrench")
                
    # DELETE MECHANIC TEST    
    def test_delete_mechanic(self):

        headers = {'Authorization': f"Bearer {self.token}"}

        response = self.client.delete(
            f'/mechanics/{self.mechanic_id}',
            headers=headers
        )
        
        self.assertEqual(response.status_code, 200)
        self.assertIn("successfully deleted", response.json["message"])

        with self.app.app_context():
            deleted_mechanic = db.session.get(
                Mechanic,
                self.mechanic_id
            )
            self.assertIsNone(deleted_mechanic)
        
# run in terminal: python -m unittest discover tests
