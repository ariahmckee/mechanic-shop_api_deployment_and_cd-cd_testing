from app import create_app
from app.models import Customer, Inventory, db, Mechanic, Ticket
from app.utils.util import encode_token, encode_mechanic_token
from datetime import date
import unittest

class TestTicket(unittest.TestCase):
    def setUp(self):
        self.app = create_app("TestingConfig")
        self.customer = Customer(
            name="test_user", 
            email="test@email.com", 
            phone="1111111111" , 
            password='test'
            )
        self.mechanic = Mechanic(
            name="test_user",
            email="test@email.com",
            phone="1111111111",
            password="test",
            salary=60000
        )
        self.ticket = Ticket(
            vin="TESTVIN000000001",
            ticket_date=date(2026, 7, 23),
            ticket_desc="Windshield Lubrication",
            customer=self.customer
        )
        self.inventory = Inventory(
            name="Flubber Deregulator",
            price=60.00
        )
        with self.app.app_context():
            db.drop_all()
            db.create_all()
            db.session.add_all([self.customer, self.mechanic, self.ticket, self.inventory])
            db.session.commit()

            self.customer_id = self.customer.id
            self.mechanic_id = self.mechanic.id
            self.ticket_id = self.ticket.id
            self.inventory_id = self.inventory.id
            
        self.customer_token = encode_token(self.customer_id)
        self.mechanic_token = encode_mechanic_token(self.mechanic_id)
        self.client = self.app.test_client()
    

    # CREATE TICKET TESTS
    def test_create_ticket(self):
        ticket_payload = {
            "vin": "TESTVIN000000001",
            "ticket_date": "2026-07-23",
            "ticket_desc": "Windshield Lubrication",
            "customer_id": self.customer_id
        }
        
        response = self.client.post('/tickets/', json=ticket_payload)

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json['vin'], "TESTVIN000000001")
        self.assertEqual(response.json['ticket_desc'], "Windshield Lubrication")
        self.assertEqual(response.json['customer_id'], self.customer_id)
        
    def test_invalid_ticket_creation(self):
        ticket_payload = {
            "ticket_date": "2026-07-23",
            "ticket_desc": "Windshield Lubrication",
            "customer_id": self.customer_id
        }

        response = self.client.post('/tickets/', json=ticket_payload)

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json['vin'], ['Missing data for required field.'])

    # GET ALL CUSTOMER'S TICKETs TEST    
    def test_get_my_tickets(self):
        
        headers = {'Authorization': f"Bearer {self.customer_token}"}
        
        response = self.client.get(
            '/tickets/my-tickets', 
            headers=headers
            )
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json), 1)
        self.assertEqual(response.json[0]['vin'], "TESTVIN000000001")
        self.assertEqual(response.json[0]['ticket_desc'], "Windshield Lubrication")
        self.assertEqual(response.json[0]['customer_id'], self.customer_id)
        
    # GET SPECIFIC TICKET TEST    
    def test_get_ticket(self):
        response = self.client.get(f"/tickets/{self.ticket_id}")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json['vin'], "TESTVIN000000001")
        self.assertEqual(response.json['ticket_desc'], "Windshield Lubrication")
        self.assertEqual(response.json['customer_id'], self.customer_id)

    # UPDATE TICKET TEST    
    def test_update_ticket(self):
        update_payload = {
            "vin": "TESTVIN000000001",
            "ticket_date": "2026-07-24",
            "ticket_desc": "Windshield De-Lubrication",
            "customer_id": self.customer_id
        }

        response = self.client.put(
            f'/tickets/{self.ticket_id}',
            json=update_payload
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json['ticket_date'], '2026-07-24')
        self.assertEqual(response.json['ticket_desc'], 'Windshield De-Lubrication') 

        with self.app.app_context():
            updated_ticket = db.session.get(Ticket, self.ticket_id)
            self.assertEqual(updated_ticket.ticket_date, date(2026, 7, 24))
            self.assertEqual(updated_ticket.ticket_desc, "Windshield De-Lubrication")

    # EDIT MECHANICS ASSOCIATED TO A TICKET TEST    
    def test_edit_ticket_mechanics(self):
        new_mechanic = Mechanic(
            name="Second Mechanic",
            email="second@email.com",
            phone="2222222222",
            password="test",
            salary=55000
        )
        with self.app.app_context():
            ticket = db.session.get(Ticket, self.ticket_id)
            mechanic = db.session.get(Mechanic, self.mechanic_id)

            ticket.mechanics.append(mechanic)
            db.session.add(new_mechanic)
            db.session.commit()

            new_mechanic_id = new_mechanic.id
        
        update_payload = {
            "add_ids": [new_mechanic_id],
            "remove_ids": [self.mechanic_id]
        }

        response = self.client.put(
            f'/tickets/{self.ticket_id}/edit',
            json=update_payload
        )
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json["mechanic_ids"],
            [new_mechanic_id]
        )
        
        with self.app.app_context():
            updated_ticket = db.session.get(
                Ticket,
                self.ticket_id
            )
            
            mechanic_ids = [
                mechanic.id
                for mechanic in updated_ticket.mechanics
            ]
            
            
            self.assertIn(new_mechanic_id, mechanic_ids)
            self.assertNotIn(self.mechanic_id, mechanic_ids)

    # ADD PART FROM INVENTORY TO TICKET TEST    
    def test_add_part_to_ticket(self):
        update_payload = {
            "quantity": 20
        }
        headers = {'Authorization': f"Bearer {self.mechanic_token}"}
        
        response = self.client.put(
            f'/tickets/{self.ticket_id}/add-part/{self.inventory_id}',
            json=update_payload,
            headers=headers
        )
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json["inventory_items"]), 1)
        
        added_part = response.json["inventory_items"][0]
        
        self.assertEqual(added_part["inventory_id"], self.inventory_id)
        self.assertEqual(added_part["name"], "Flubber Deregulator")
        self.assertEqual(added_part["price"], 60.0)
        self.assertEqual(added_part["quantity"], 20)

    # DELETE TICKET TEST
    def test_delete_ticket(self):

        headers = {'Authorization': f"Bearer {self.mechanic_token}"}

        response = self.client.delete(
            f'/tickets/{self.ticket_id}',
            headers=headers
        )
        
        self.assertEqual(response.status_code, 200)
        self.assertIn("successfully deleted", response.json["message"])

        with self.app.app_context():
            deleted_ticket = db.session.get(
                Ticket,
                self.ticket_id
            )
            self.assertIsNone(deleted_ticket)
        
# run in terminal: python -m unittest discover tests
