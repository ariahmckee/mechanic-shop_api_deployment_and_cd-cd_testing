from app import create_app
from app.models import db, Inventory, Mechanic
from app.utils.util import encode_mechanic_token
import unittest

class TestInventory(unittest.TestCase):
    def setUp(self):
        self.app = create_app("TestingConfig")
        self.inventory = Inventory(
            name="Flubber Deregulator",
            price=60.00
        )
        self.mechanic = Mechanic(
            name="Test Mechanic",
            email="mechanic@email.com",
            phone="1111111111",
            password="test",
            salary=60000
        )
        with self.app.app_context():
            db.drop_all()
            db.create_all()
            db.session.add_all([self.inventory, self.mechanic])
            db.session.commit()
            
            self.inventory_id = self.inventory.id
            self.mechanic_id = self.mechanic.id
            
        self.token = encode_mechanic_token(self.mechanic_id)
        self.client = self.app.test_client()
    

    # CREATE INVENTORY ITEM TESTS    
    def test_create_inventory(self):
        inventory_payload = {
            "name": "Flubber Deregulator",
            "price": 60.00
        }
        headers = {'Authorization': f"Bearer {self.token}"}

        response = self.client.post(
            '/inventory/',
            json=inventory_payload,
            headers=headers
        )

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json['name'], "Flubber Deregulator")
        
    def test_invalid_creation(self):
        inventory_payload = {
            "name": "Flubber Deregulator"
        }
        headers = {'Authorization': f"Bearer {self.token}"}

        response = self.client.post(
            '/inventory/',
            json=inventory_payload,
            headers=headers
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json['price'], ['Missing data for required field.'])
    
    # UPDATE TEST    
    def test_update_inventory(self):
        update_payload = {
            "name": "Flubber Deregulator",
            "price": 4.00
        }

        headers = {'Authorization': f"Bearer {self.token}"}

        response = self.client.put(
            f'/inventory/{self.inventory_id}',
            json=update_payload,
            headers=headers
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json['name'], 'Flubber Deregulator') 
        self.assertEqual(response.json['price'], 4.0)

        with self.app.app_context():
            updated_inventory = db.session.get(Inventory, self.inventory_id)
            self.assertEqual(updated_inventory.name, "Flubber Deregulator")
            self.assertEqual(updated_inventory.price, 4.0)

    # GET INVENTORY TEST    
    def test_get_inventory(self):
        response = self.client.get('/inventory/')
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json), 1)
        self.assertEqual(
            response.json[0]["name"],
            "Flubber Deregulator"
        )
        
    # GET SPECIFIC INVENTORY ITEM TEST    
    def test_get_inventory_item(self):
        response = self.client.get(f"/inventory/{self.inventory_id}")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json["id"], self.inventory_id)
        self.assertEqual(response.json["name"], "Flubber Deregulator")
                
    # DELETE INVENTORY ITEM TEST    
    def test_delete_inventory(self):

        headers = {'Authorization': f"Bearer {self.token}"}

        response = self.client.delete(
            f'/inventory/{self.inventory_id}',
            headers=headers
        )
        
        self.assertEqual(response.status_code, 200)
        self.assertIn("successfully deleted", response.json["message"])

        with self.app.app_context():
            deleted_inventory = db.session.get(
                Inventory,
                self.inventory_id
            )
            self.assertIsNone(deleted_inventory)
        
# run in terminal: python -m unittest discover tests
