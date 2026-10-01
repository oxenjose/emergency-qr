import uuid
from werkzeug.security import generate_password_hash, check_password_hash
from database.db import get_db

# Column order as defined in the contacts table (used to convert tuples to dicts)
CONTACT_COLUMNS = [
    'id', 'owner_name', 'label',
    'name1', 'phone1', 'name2', 'phone2', 'name3', 'phone3',
    'pin_hash', 'created_at'
]

def create_contact(owner_name, label, name1, phone1, name2, phone2, name3, phone3, pin):
    contact_id = str(uuid.uuid4())
    pin_hash = generate_password_hash(pin)
    db = get_db()
    db.execute('''
        INSERT INTO contacts
            (id, owner_name, label, name1, phone1, name2, phone2, name3, phone3, pin_hash)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (contact_id, owner_name, label, name1, phone1, name2, phone2, name3, phone3, pin_hash))
    db.commit()
    return contact_id

def get_contact(contact_id):
    db = get_db()
    cursor = db.execute('SELECT * FROM contacts WHERE id = ?', (contact_id,))
    row = cursor.fetchone()
    if row is None:
        return None
    # libsql returns plain tuples — convert to dict using known column order
    return dict(zip(CONTACT_COLUMNS, row))

def update_contact(contact_id, owner_name, label, name1, phone1, name2, phone2, name3, phone3):
    db = get_db()
    db.execute('''
        UPDATE contacts
        SET owner_name = ?, label = ?,
            name1 = ?, phone1 = ?, name2 = ?, phone2 = ?, name3 = ?, phone3 = ?
        WHERE id = ?
    ''', (owner_name, label, name1, phone1, name2, phone2, name3, phone3, contact_id))
    db.commit()

def verify_pin(contact_id, pin):
    contact = get_contact(contact_id)
    if contact:
        return check_password_hash(contact['pin_hash'], pin)
    return False