from marshmallow import fields, validate
from app.extensions import ma
from app.models import Ticket


class TicketSchema(ma.SQLAlchemyAutoSchema):
    mechanic_ids = ma.Method("get_mechanic_ids", dump_only=True)
    inventory_items = ma.Method("get_inventory_items", dump_only=True)
    
    class Meta:
        model = Ticket
        include_fk = True
        
    def get_mechanic_ids(self, ticket):
        return [mechanic.id for mechanic in ticket.mechanics]
    
    def get_inventory_items(self, ticket):
        return [
            {
                "inventory_id": item.inventory_id,
                "name": item.inventory.name,
                "price": item.inventory.price,
                "quantity": item.quantity
            }
            for item in ticket.inventory_items
        ]
    
class EditTicketSchema(ma.Schema):
    add_ids = fields.List(fields.Int(), required=True)
    remove_ids = fields.List(fields.Int(), required=True)
    class Meta:
        fields = ("add_ids", "remove_ids")

class AddPartSchema(ma.Schema):
    quantity = fields.Int(load_default=1, validate=validate.Range(min=1))

ticket_schema = TicketSchema()
tickets_schema = TicketSchema(many=True)
return_ticket_schema = TicketSchema (exclude=["customer_id"])
edit_ticket_schema = EditTicketSchema()
add_part_schema = AddPartSchema()
