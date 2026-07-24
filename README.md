# Mechanic Shop API

A production-ready Flask REST API for managing a mechanic shop's customers, mechanics, service tickets, and parts inventory. It includes JWT-based authorization, Swagger documentation, automated tests, a PostgreSQL production configuration, and a GitHub Actions CI/CD pipeline for deployment to Render.

## Features

- Customer, mechanic, ticket, and inventory CRUD routes
- Customer login with JWT access to the customer's own tickets
- Mechanic login with mechanic-only JWT access for protected mechanic and inventory actions
- Rate limiting on selected routes plus default app-wide rate limits
- Cached read routes with Flask-Caching
- Ticket mechanic assignment through `PUT /tickets/<ticket_id>/edit`
- Inventory parts connected to tickets through a quantity-aware `ticket_inventory` model
- Interactive Swagger API documentation for every endpoint
- Assignment-scoped unittest coverage for every route, with representative negative and authenticated-route tests
- Postman collection included for route testing

## Tech Stack

- Python
- Flask
- Flask-SQLAlchemy
- Flask-Marshmallow
- Flask-Limiter
- Flask-Caching
- Flask-Swagger-UI
- python-jose
- MySQL Connector/Python
- MySQL
- unittest with SQLite for isolated route testing

## Project Structure

```text
app/
  blueprints/
    customers/
    inventory/
    mechanics/
    tickets/
  utils/
    util.py
  static/
    swagger.yaml
  __init__.py
  extensions.py
  models.py
tests/
  test_customer.py
  test_inventory.py
  test_mechanic.py
  test_ticket.py
flask_app.py
config.py
requirements.txt
mechanic-shop.postman_collection.json
```

## Setup

Create and activate a virtual environment:

```bash
python -m venv venv
source venv/bin/activate
```

If VS Code displays unresolved-import warnings, select the project interpreter with **Python: Select Interpreter**:

```text
<project-folder>/venv/bin/python
```

Install dependencies:

```bash
python -m pip install -r requirements.txt
```

Create the MySQL database:

```sql
CREATE DATABASE mechanic_db;
```

Update the database URI in `config.py` to match your local MySQL username, password, host, and database.

Run the app locally with a development configuration:

```bash
flask --app 'app:create_app("DevelopmentConfig")' run
```

The API runs at:

```text
http://127.0.0.1:5000
```

For Render, set `DATABASE_URI` and `SECRET_KEY` as environment variables and use this start command:

```bash
gunicorn flask_app:app
```

Note: `db.create_all()` creates missing tables, but it does not update existing table schemas. If you add new columns to an existing local database, update the table manually in MySQL Workbench or recreate the database.

## API Documentation

After starting the application, open the interactive Swagger UI at:

```text
http://127.0.0.1:5000/api/docs/
```

The OpenAPI specification is stored in `app/static/swagger.yaml` and documents request payloads, response shapes, authentication requirements, and examples for each endpoint.

## Testing

The test suite uses Python's built-in `unittest` library and the SQLite database configured by `TestingConfig`. Each test resets the database and seeds any customers, mechanics, tickets, or inventory records required by the route.

Run every test from the project root:

```bash
python -m unittest discover tests
```

Run the tests with individual test names and results:

```bash
python -m unittest discover tests -v
```

The suite currently contains 33 tests across four test files. It includes at least one test for every API route, negative payload and login tests, token-authenticated route tests, mechanic ownership checks, and ticket relationship tests.

## Authentication

Customer login:

```text
POST /customers/login
```

```json
{
  "email": "customer@example.com",
  "password": "1234"
}
```

Mechanic login:

```text
POST /mechanics/login
```

```json
{
  "email": "mechanic@example.com",
  "password": "1234"
}
```

Protected routes use a Bearer token:

```text
Authorization: Bearer <token>
```

Customer tokens and mechanic tokens are intentionally separate.

## Routes

### Customers

| Method | Endpoint | Description |
| --- | --- | --- |
| POST | `/customers/` | Create a customer |
| POST | `/customers/login` | Log in a customer |
| GET | `/customers/?page=1&per_page=10` | Get paginated customers |
| GET | `/customers/<customer_id>` | Get one customer |
| PUT | `/customers/` | Update logged-in customer |
| DELETE | `/customers/` | Delete logged-in customer |

Example customer payload:

```json
{
  "name": "Ada Lovelace",
  "email": "ada@example.com",
  "phone": "1112223333",
  "password": "1234"
}
```

### Mechanics

| Method | Endpoint | Description |
| --- | --- | --- |
| POST | `/mechanics/` | Create a mechanic |
| POST | `/mechanics/login` | Log in a mechanic |
| GET | `/mechanics/` | Get all mechanics |
| GET | `/mechanics/<mechanic_id>` | Get one mechanic |
| PUT | `/mechanics/<mechanic_id>` | Update logged-in mechanic |
| DELETE | `/mechanics/<mechanic_id>` | Delete logged-in mechanic |
| GET | `/mechanics/experience` | Get mechanics ordered by tickets worked |
| GET | `/mechanics/search?name=<name>` | Search mechanics by name |

Example mechanic payload:

```json
{
  "name": "Gino Jet",
  "email": "gjet@example.com",
  "phone": "2223334444",
  "password": "1234",
  "salary": 90000
}
```

### Tickets

| Method | Endpoint | Description |
| --- | --- | --- |
| POST | `/tickets/` | Create a ticket |
| GET | `/tickets/my-tickets` | Get tickets for the logged-in customer |
| GET | `/tickets/<ticket_id>` | Get one ticket |
| PUT | `/tickets/<ticket_id>` | Update a ticket |
| DELETE | `/tickets/<ticket_id>` | Delete a ticket |
| PUT | `/tickets/<ticket_id>/edit` | Add and remove mechanics on a ticket |
| PUT | `/tickets/<ticket_id>/add-part/<inventory_id>` | Add an inventory part to a ticket |

Example ticket payload:

```json
{
  "vin": "ABCDEFGHIJKL1234567890",
  "ticket_date": "1900-10-10",
  "ticket_desc": "Added NOS to the chair recline motor",
  "customer_id": 1
}
```

Example mechanic edit payload:

```json
{
  "add_ids": [2, 3],
  "remove_ids": [1]
}
```

Example add-part payload:

```json
{
  "quantity": 2
}
```

Example ticket response:

```json
{
  "id": 1,
  "vin": "ABCDEFGHIJKL1234567890",
  "ticket_date": "1900-10-10",
  "ticket_desc": "Added NOS to the chair recline motor",
  "customer_id": 1,
  "mechanic_ids": [2, 3],
  "inventory_items": [
    {
      "inventory_id": 1,
      "name": "NOS",
      "price": 12.5,
      "quantity": 2
    }
  ]
}
```

### Inventory

| Method | Endpoint | Description |
| --- | --- | --- |
| POST | `/inventory/` | Create an inventory part |
| GET | `/inventory/` | Get all inventory parts |
| GET | `/inventory/<inventory_id>` | Get one inventory part |
| PUT | `/inventory/<inventory_id>` | Update an inventory part |
| DELETE | `/inventory/<inventory_id>` | Delete an inventory part |

Example inventory payload:

```json
{
  "name": "NOS",
  "price": 12.5
}
```

Inventory create, update, and delete routes require a mechanic Bearer token.

## Postman

Use `mechanic-shop.postman_collection.json` to test the API routes. For protected routes, first run the relevant login request, then paste the returned token into the request's Bearer Token auth field.

## Notes

- `customer_id` is required when creating or updating a ticket.
- Mechanic and customer email and phone values must be unique.
- `mechanic_ids` is returned in ticket responses and can be managed through `/tickets/<ticket_id>/edit`.
- `inventory_items` is returned in ticket responses and can be managed through `/tickets/<ticket_id>/add-part/<inventory_id>`.
